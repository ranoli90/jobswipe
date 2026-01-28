"""
Cleanup Background Tasks

Celery tasks for database maintenance and cleanup operations.
"""

import logging
from datetime import datetime, timedelta

from db.database import get_db
from db.models import (OAuth2State, RefreshToken, Session,
                               UserJobInteraction)
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Cleanup configuration constants
DEFAULT_EXPIRED_TOKENS_DAYS = 1
DEFAULT_OLD_SESSIONS_DAYS = 7
DEFAULT_EXPIRED_OAUTH_STATES_HOURS = 1
DEFAULT_OLD_INTERACTIONS_DAYS = 90
DEFAULT_ORPHAN_NOTIFICATIONS_DAYS = 30
DEFAULT_TEMP_FILES_HOURS = 24
TEMPORARY_DIRECTORIES = ["/tmp/reports", "/tmp/uploads", "/tmp/cache"]
MAX_INTERACTIONS_TO_ARCHIVE = 10000
CELERY_TASK_TIMEOUT = 60


@celery_app.task
def cleanup_expired_tokens(days: int = DEFAULT_EXPIRED_TOKENS_DAYS):
    """
    Clean up expired JWT refresh tokens.

    Args:
        days: Only tokens older than this will be deleted

    Returns:
        Number of tokens deleted
    """
    db = next(get_db())
    deleted = 0

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Delete expired tokens
        result = (
            db.query(RefreshToken).filter(RefreshToken.expires_at < cutoff).delete()
        )

        db.commit()
        deleted = result
        logger.info("Cleaned up %s expired refresh tokens", deleted)
        return deleted

    except Exception as e:
        logger.error("Error cleaning up expired tokens: %s", e)
        db.rollback()
        return 0
    finally:
        db.close()


@celery_app.task
def cleanup_old_sessions(days: int = DEFAULT_OLD_SESSIONS_DAYS):
    """
    Clean up old user sessions.

    Args:
        days: Only sessions older than this will be deleted

    Returns:
        Number of sessions deleted
    """
    db = next(get_db())
    deleted = 0

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Delete old sessions
        result = db.query(Session).filter(Session.created_at < cutoff).delete()

        db.commit()
        deleted = result
        logger.info("Cleaned up %s old sessions", deleted)
        return deleted

    except Exception as e:
        logger.error("Error cleaning up old sessions: %s", e)
        db.rollback()
        return 0
    finally:
        db.close()


@celery_app.task
def cleanup_expired_oauth_states(hours: int = DEFAULT_EXPIRED_OAUTH_STATES_HOURS):
    """
    Clean up expired OAuth2 state tokens.

    Args:
        hours: Only states older than this will be deleted

    Returns:
        Number of states deleted
    """
    db = next(get_db())
    deleted = 0

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Delete expired states
        result = db.query(OAuth2State).filter(OAuth2State.created_at < cutoff).delete()

        db.commit()
        deleted = result
        logger.info("Cleaned up %s expired OAuth2 states", deleted)
        return deleted

    except Exception as e:
        logger.error("Error cleaning up OAuth2 states: %s", e)
        db.rollback()
        return 0
    finally:
        db.close()


@celery_app.task
def cleanup_old_interactions(days: int = DEFAULT_OLD_INTERACTIONS_DAYS):
    """
    Archive or delete old user interactions.

    Args:
        days: Only interactions older than this will be processed

    Returns:
        Number of interactions archived
    """
    db = next(get_db())
    archived = 0

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get interactions to archive
        interactions = (
            db.query(UserJobInteraction)
            .filter(UserJobInteraction.created_at < cutoff)
            .limit(MAX_INTERACTIONS_TO_ARCHIVE)
            .all()
        )

        if not interactions:
            return 0

        # In a real implementation, you would:
        # 1. Export to cold storage (S3, etc.)
        # 2. Delete from database
        # For now, just log them
        for interaction in interactions:
            # Mark as archived (you might add an is_archived field)
            archived += 1

        logger.info("Archived %s old interactions (dry run - not actually deleted)" % (archived)
        )
        return archived

    except Exception as e:
        logger.error("Error archiving old interactions: %s", e)
        return 0
    finally:
        db.close()


@celery_app.task
def cleanup_orphan_notifications(days: int = DEFAULT_ORPHAN_NOTIFICATIONS_DAYS):
    """
    Clean up notifications for deleted users.

    Args:
        days: Only notifications older than this will be deleted

    Returns:
        Number of notifications deleted
    """
    db = next(get_db())
    deleted = 0

    try:
        from db.models import Notification, User

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get notifications for non-existent users
        orphan_notifications = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff)
            .outerjoin(User, Notification.user_id == User.id)
            .filter(User.id.is_(None))
        )

        deleted = orphan_notifications.count()
        orphan_notifications.delete(synchronize_session=False)

        db.commit()
        logger.info("Cleaned up %s orphan notifications", deleted)
        return deleted

    except Exception as e:
        logger.error("Error cleaning up orphan notifications: %s", e)
        db.rollback()
        return 0
    finally:
        db.close()


@celery_app.task
def cleanup_temp_files(hours: int = DEFAULT_TEMP_FILES_HOURS):
    """
    Clean up temporary files older than specified hours.

    Args:
        hours: Only files older than this will be deleted

    Returns:
        Number of files deleted
    """
    import glob
    import os

    deleted = 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    temp_dirs = TEMPORARY_DIRECTORIES

    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue

        for file_path in glob.glob(f"{temp_dir}/*"):
            if not os.path.isfile(file_path):
                continue

            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < cutoff:
                try:
                    os.remove(file_path)
                    deleted += 1
                except Exception as e:
                    logger.warning("Could not delete %s: %s", file_path, e)

    logger.info("Cleaned up %s temporary files", deleted)
    return deleted


@celery_app.task
def run_all_cleanup_tasks():
    """
    Run all cleanup tasks sequentially.

    Returns:
        Summary of all cleanup operations
    """
    results = {}

    try:
        results["expired_tokens"] = cleanup_expired_tokens.delay().get(timeout=CELERY_TASK_TIMEOUT)
        results["old_sessions"] = cleanup_old_sessions.delay().get(timeout=CELERY_TASK_TIMEOUT)
        results["oauth_states"] = cleanup_expired_oauth_states.delay().get(timeout=CELERY_TASK_TIMEOUT)
        results["orphan_notifications"] = cleanup_orphan_notifications.delay().get(
            timeout=CELERY_TASK_TIMEOUT
        )
        results["temp_files"] = cleanup_temp_files.delay().get(timeout=CELERY_TASK_TIMEOUT)

        logger.info("Completed all cleanup tasks: %s", results)
        return results

    except Exception as e:
        logger.error("Error running cleanup tasks: %s", e)
        return {"error": str(e)}
