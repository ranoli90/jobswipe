"""
Notification Background Tasks

Celery tasks for handling email and push notifications.
"""

import logging
from datetime import datetime, timedelta

from backend.db.database import get_db
from backend.db.models import Notification, NotificationPreference, User
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(
    self, user_id: str, subject: str, body: str, notification_type: str = "info"
):
    """
    Send email notification to a user.

    Args:
        user_id: User ID to send notification to
        subject: Email subject
        body: Email body
        notification_type: Type of notification (info, warning, error, success)
    """
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("User %s not found for email notification", user_id)
            return {"status": "failed", "reason": "User not found"}

        # Log notification (in production, integrate with email service like SendGrid, SES, etc.)
        logger.info("Sending email to %s: %s", user.email, subject)

        # Create notification record
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=subject,
            message=body,
            is_read=False,
        )
        db.add(notification)
        db.commit()

        return {"status": "sent", "user_id": user_id, "email": user.email}

    except Exception as e:
        logger.error("Failed to send email notification to %s: %s", user_id, e)
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_push_notification(
    self, user_id: str, title: str, message: str, data: dict = None
):
    """
    Send push notification to a user.

    Args:
        user_id: User ID to send notification to
        title: Notification title
        message: Notification message
        data: Additional data payload
    """
    db = next(get_db())
    try:
        # Get user's push notification preferences
        prefs = (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )

        if prefs and not prefs.push_enabled:
            logger.info("Push notifications disabled for user %s", user_id)
            return {"status": "skipped", "reason": "Push disabled"}

        # In production, integrate with FCM, APNS, etc.
        logger.info("Sending push to user %s: %s", user_id, title)

        # Create notification record
        notification = Notification(
            user_id=user_id,
            type="push",
            title=title,
            message=message,
            metadata=data or {},
            is_read=False,
        )
        db.add(notification)
        db.commit()

        return {"status": "sent", "user_id": user_id}

    except Exception as e:
        logger.error("Failed to send push notification to %s: %s", user_id, e)
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task
def send_daily_digest():
    """
    Send daily digest emails to users who have opted in.

    Returns:
        Number of digests sent
    """
    db = next(get_db())
    digests_sent = 0

    try:
        # Get users with daily digest enabled
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        users = db.query(User).all()

        for user in users:
            # Check user's notification preferences
            prefs = (
                db.query(NotificationPreference)
                .filter(NotificationPreference.user_id == user.id)
                .first()
            )

            if prefs and not prefs.daily_digest_enabled:
                continue

            # Count new jobs and applications for the day
            from backend.db.models import ApplicationTask, Job

            new_jobs = db.query(Job).filter(Job.created_at >= yesterday).count()

            applications = (
                db.query(ApplicationTask)
                .filter(
                    ApplicationTask.user_id == user.id,
                    ApplicationTask.created_at >= yesterday,
                )
                .count()
            )

            if new_jobs > 0 or applications > 0:
                # Queue the email
                send_email_notification.delay(
                    user.id,
                    f"Daily Job Digest - {today}",
                    f"You have {new_jobs} new jobs and {applications} application updates.",
                    "digest",
                )
                digests_sent += 1

        logger.info("Sent %s daily digest emails", digests_sent)
        return digests_sent

    except Exception as e:
        logger.error("Error sending daily digest: %s", e)
        return 0
    finally:
        db.close()


@celery_app.task
def send_application_status_update(
    user_id: str, application_id: str, status: str, message: str
):
    """
    Send notification about application status update.

    Args:
        user_id: User ID
        application_id: Application task ID
        status: New status
        message: Status message
    """
    return send_email_notification.delay(
        user_id, f"Application Update - {status}", message, "application_update"
    )


@celery_app.task
def send_new_match_notification(user_id: str, job_id: str, match_score: float):
    """
    Send notification when a high-match job is found.

    Args:
        user_id: User ID
        job_id: Job ID
        match_score: Match score (0-1)
    """
    if match_score < 0.7:
        return {"status": "skipped", "reason": "Match score too low"}

    return send_push_notification.delay(
        user_id,
        "New High-Match Job!",
        f"You have a {int(match_score * 100)}% match for a new job!",
        {"job_id": job_id, "match_score": match_score},
    )
