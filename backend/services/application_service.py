"""
Application Service

Handles job application task management and automation.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from backend.db.database import get_db
from backend.db.models import (ApplicationAuditLog, ApplicationTask,
                               CandidateProfile, Job)
from workers.application_agent.agents.greenhouse import (
    ApplicationLogger, GreenhouseAgent, LeverAgent)

logger = logging.getLogger(__name__)


async def create_application_task(
    user_id: str, job_id: str, db=None
) -> ApplicationTask:
    """
    Create an application task for a job.

    Args:
        user_id: User ID
        job_id: Job ID
        db: Database session

    Returns:
        ApplicationTask object
    """
    if db is None:
        db = next(get_db())

    try:
        # Check if task already exists
        existing_task = (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.user_id == user_id, ApplicationTask.job_id == job_id
            )
            .first()
        )

        if existing_task:
            logger.warning("Application task already exists for user %s and job %s" % (user_id, job_id)
            )
            return existing_task

        # Create new task
        task = ApplicationTask(
            id=uuid.uuid4(), user_id=user_id, job_id=job_id, status="queued"
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info("Created application task: %s", task.id)

        return task

    except Exception as e:
        if db:
            db.rollback()
        logger.error("Error creating application task: %s", str(e))
        raise


async def run_application_task(task_id: str, db=None):
    """
    Run application task automation.

    Args:
        task_id: Application task ID
        db: Database session

    Returns:
        Boolean indicating success
    """
    resume_path = None
    
    if db is None:
        db = next(get_db())

    try:
        task = db.query(ApplicationTask).filter(ApplicationTask.id == task_id).first()

        if not task:
            logger.error("Application task not found: %s", task_id)
            return False

        # Get job and profile
        job = db.query(Job).filter(Job.id == task.job_id).first()
        profile = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == task.user_id)
            .first()
        )

        if not job or not profile:
            logger.error("Job or profile not found for task %s", task_id)
            task.status = "failed"
            task.last_error = "Job or profile not found"
            db.add(task)
            db.commit()
            return False

        # Initialize logger
        audit_logger = ApplicationLogger(str(task.id))

        # Get resume path
        resume_path = None
        if profile.resume_file_url:
            from services.storage import download_file

            resume_content = download_file(profile.resume_file_url)

            if resume_content:
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="wb", suffix=".pdf", delete=False
                ) as f:
                    f.write(resume_content)
                    resume_path = f.name

        if not resume_path:
            logger.error("No resume found for user %s", task.user_id)
            task.status = "failed"
            task.last_error = "No resume found"
            db.add(task)
            db.commit()
            return False

        # Select ATS agent based on job source
        success = False
        error = None

        print(f"DEBUG: job.source = '{getattr(job, 'source', 'NONE')}', type = {type(getattr(job, 'source', 'NONE'))}")
        if job.source == "greenhouse":
            success, error = await GreenhouseAgent.apply(
                job.apply_url,
                {
                    "full_name": profile.full_name,
                    "email": "test@example.com",  # Need to get from user model
                    "phone": profile.phone,
                    "location": profile.location,
                },
                resume_path,
                audit_logger,
            )
            # Update task status based on success
            task.attempt_count += 1
            if success:
                task.status = "success"
                logger.info("Application task completed successfully: %s", task_id)
            else:
                if error and ("CAPTCHA" in error or "captcha" in error):
                    task.status = "waiting_human"
                    task.last_error = error
                    logger.warning("CAPTCHA detected for task %s: %s", task_id, error)
                else:
                    task.status = "failed"
                    task.last_error = error
                    logger.error("Application task failed: %s - %s", task_id, error)
            db.add(task)
            db.commit()
            return success
        elif job.source == "lever":
            success, error = await LeverAgent.apply(
                job.apply_url,
                {
                    "full_name": profile.full_name,
                    "email": "test@example.com",
                    "phone": profile.phone,
                    "location": profile.location,
                },
                resume_path,
                audit_logger,
            )
            # Update task status based on success
            task.attempt_count += 1
            if success:
                task.status = "success"
                logger.info("Application task completed successfully: %s", task_id)
            else:
                if error and ("CAPTCHA" in error or "captcha" in error):
                    task.status = "waiting_human"
                    task.last_error = error
                    logger.warning("CAPTCHA detected for task %s: %s", task_id, error)
                else:
                    task.status = "failed"
                    task.last_error = error
                    logger.error("Application task failed: %s - %s", task_id, error)
            db.add(task)
            db.commit()
            return success
        else:
            logger.warning("Unknown job source: %s", job.source)
            task.status = "needs_review"
            db.add(task)
            db.commit()
            return False
    except Exception as e:
        logger.error("Error running application task %s: %s", task_id, str(e))
        if db:
            db.rollback()
        raise

    finally:
        if resume_path:
            try:
                os.unlink(resume_path)
            except OSError:
                pass


def get_application_status(
    user_id: str, job_id: str, db=None
) -> Optional[ApplicationTask]:
    """
    Get application status for a job.

    Args:
        user_id: User ID
        job_id: Job ID
        db: Database session

    Returns:
        ApplicationTask object or None
    """
    if db is None:
        db = next(get_db())

    try:
        return (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.user_id == user_id, ApplicationTask.job_id == job_id
            )
            .first()
        )

    except Exception as e:
        logger.error("Error getting application status: %s", str(e))
        raise
    finally:
        if db:
            db.close()


def cancel_application(user_id: str, job_id: str, db=None) -> bool:
    """
    Cancel an application task.

    Args:
        user_id: User ID
        job_id: Job ID
        db: Database session

    Returns:
        Boolean indicating success
    """
    if db is None:
        db = next(get_db())

    try:
        task = (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.user_id == user_id, ApplicationTask.job_id == job_id
            )
            .first()
        )

        if not task:
            return False

        task.status = "cancelled"
        db.add(task)
        db.commit()

        logger.info("Application task cancelled: %s", task.id)

        return True

    except Exception as e:
        logger.error("Error cancelling application: %s", str(e))
        raise
    finally:
        if db:
            db.close()


def get_user_applications(user_id: str, db=None) -> list:
    """
    Get all applications for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of ApplicationTask objects
    """
    if db is None:
        db = next(get_db())

    try:
        return (
            db.query(ApplicationTask)
            .filter(ApplicationTask.user_id == user_id)
            .order_by(ApplicationTask.created_at.desc())
            .all()
        )

    except Exception as e:
        logger.error("Error getting user applications: %s", str(e))
        raise
    finally:
        if db:
            db.close()
