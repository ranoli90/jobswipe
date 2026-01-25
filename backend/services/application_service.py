"""
Application Service

Handles job application task management and automation.
"""

from typing import Optional
from backend.db.database import get_db
from backend.db.models import ApplicationTask, Job, CandidateProfile, ApplicationAuditLog
from backend.workers.application_agent.agents.greenhouse import GreenhouseAgent, LeverAgent, ApplicationLogger
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def create_application_task(user_id: str, job_id: str, db = None) -> ApplicationTask:
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
        existing_task = db.query(ApplicationTask).filter(
            ApplicationTask.user_id == user_id,
            ApplicationTask.job_id == job_id
        ).first()
        
        if existing_task:
            logger.warning(f"Application task already exists for user {user_id} and job {job_id}")
            return existing_task
            
        # Create new task
        task = ApplicationTask(
            id=uuid.uuid4(),
            user_id=user_id,
            job_id=job_id,
            status="queued"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Created application task: {task.id}")
        
        return task
        
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Error creating application task: {str(e)}")
        raise


async def run_application_task(task_id: str, db = None):
    """
    Run application task automation.
    
    Args:
        task_id: Application task ID
        db: Database session
        
    Returns:
        Boolean indicating success
    """
    if db is None:
        db = next(get_db())
        
    try:
        task = db.query(ApplicationTask).filter(ApplicationTask.id == task_id).first()
        
        if not task:
            logger.error(f"Application task not found: {task_id}")
            return False
            
        # Get job and profile
        job = db.query(Job).filter(Job.id == task.job_id).first()
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == task.user_id).first()
        
        if not job or not profile:
            logger.error(f"Job or profile not found for task {task_id}")
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
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
                    f.write(resume_content)
                    resume_path = f.name
                    
        if not resume_path:
            logger.error(f"No resume found for user {task.user_id}")
            task.status = "failed"
            task.last_error = "No resume found"
            db.add(task)
            db.commit()
            return False
            
        # Select ATS agent based on job source
        success = False
        error = None
        
        if job.source == "greenhouse":
            success, error = await GreenhouseAgent.apply(
                job.apply_url,
                {
                    "full_name": profile.full_name,
                    "email": "test@example.com",  # Need to get from user model
                    "phone": profile.phone,
                    "location": profile.location
                },
                resume_path,
                audit_logger
            )
        elif job.source == "lever":
            success, error = await LeverAgent.apply(
                job.apply_url,
                {
                    "full_name": profile.full_name,
                    "email": "test@example.com",
                    "phone": profile.phone,
                    "location": profile.location
                },
                resume_path,
                audit_logger
            )
        else:
            logger.warning(f"Unknown job source: {job.source}")
            task.status = "needs_review"
            db.add(task)
            db.commit()
            return False
            
        # Update task status
        task.attempt_count += 1
        
        if success:
            task.status = "success"
            logger.info(f"Application task completed successfully: {task_id}")
        else:
            # Check if error is CAPTCHA-related
            if "CAPTCHA" in error or "captcha" in error:
                task.status = "waiting_human"
                task.last_error = error
                logger.warning(f"CAPTCHA detected for task {task_id}: {error}")
            else:
                task.status = "failed"
                task.last_error = error
                logger.error(f"Application task failed: {task_id} - {error}")
            
        # Save audit logs
        for log_entry in audit_logger.get_logs():
            audit_log = ApplicationAuditLog(
                task_id=str(task.id),
                step=log_entry["step"],
                payload=log_entry["payload"],
                artifacts={},
                timestamp=log_entry["timestamp"]
            )
            db.add(audit_log)
            
        db.add(task)
        db.commit()
        
        # Cleanup temporary resume file
        if resume_path:
            import os
            try:
                os.unlink(resume_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary resume file: {str(e)}")
                
        return success
        
    except Exception as e:
        logger.error(f"Error running application task {task_id}: {str(e)}")
        
        if db:
            task = db.query(ApplicationTask).filter(ApplicationTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.attempt_count += 1
                task.last_error = str(e)
                db.add(task)
                
                # Add error to audit log
                audit_log = ApplicationAuditLog(
                    task_id=str(task.id),
                    step="error",
                    payload={"message": str(e)},
                    artifacts={},
                    timestamp=datetime.utcnow().isoformat()
                )
                db.add(audit_log)
                
                db.commit()
                
        return False
    finally:
        if db:
            db.close()


def get_application_status(user_id: str, job_id: str, db = None) -> Optional[ApplicationTask]:
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
        return db.query(ApplicationTask).filter(
            ApplicationTask.user_id == user_id,
            ApplicationTask.job_id == job_id
        ).first()
        
    except Exception as e:
        logger.error(f"Error getting application status: {str(e)}")
        raise
    finally:
        if db:
            db.close()


def cancel_application(user_id: str, job_id: str, db = None) -> bool:
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
        task = db.query(ApplicationTask).filter(
            ApplicationTask.user_id == user_id,
            ApplicationTask.job_id == job_id
        ).first()
        
        if not task:
            return False
            
        task.status = "cancelled"
        db.add(task)
        db.commit()
        
        logger.info(f"Application task cancelled: {task.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error cancelling application: {str(e)}")
        raise
    finally:
        if db:
            db.close()


def get_user_applications(user_id: str, db = None) -> list:
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
        return db.query(ApplicationTask).filter(
            ApplicationTask.user_id == user_id
        ).order_by(ApplicationTask.created_at.desc()).all()
        
    except Exception as e:
        logger.error(f"Error getting user applications: {str(e)}")
        raise
    finally:
        if db:
            db.close()
