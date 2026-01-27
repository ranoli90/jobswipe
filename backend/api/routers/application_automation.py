"""
Application Automation Router

Provides endpoints for managing automated job applications.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.api.routers.auth import get_current_user
from backend.config import settings
from backend.db.database import get_db
from backend.db.models import ApplicationTask, CandidateProfile, Job, User
from backend.services.application_automation import \
    application_automation_service
from backend.services.cover_letter_service import cover_letter_service
from backend.services.domain_service import domain_service
from backend.services.job_ingestion_service import job_ingestion_service

router = APIRouter()
logger = logging.getLogger(__name__)

security = HTTPBearer()

# API key for automation operations
AUTOMATION_API_KEY = settings.automation_api_key


class ApplicationAutomationRequest(BaseModel):
    """Request model for automated application"""

    task_id: str
    headless: bool = True


class ApplicationAutomationResponse(BaseModel):
    """Response model for automated application"""

    success: bool
    task_id: str
    status: str
    message: str
    submitted: bool
    timestamp: str


class TaskStatusUpdate(BaseModel):
    """Request model for updating task status"""

    status: str
    last_error: Optional[str] = None


class CoverLetterRequest(BaseModel):
    """Request model for cover letter generation"""

    job_id: str
    custom_instructions: Optional[str] = None


class CoverLetterResponse(BaseModel):
    """Response model for cover letter generation"""

    success: bool
    cover_letter: str
    word_count: int
    error: str
    metadata: Dict[str, Any]


class CoverLetterRegenerateRequest(BaseModel):
    """Request model for cover letter regeneration"""

    job_id: str
    previous_letter: str
    feedback: str
    custom_instructions: Optional[str] = None


class NotificationRequest(BaseModel):
    """Request model for sending notifications"""

    task_id: str
    notification_type: (
        str  # "captcha_detected", "application_failed", "rate_limited", etc.
    )
    message: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/auto-apply", response_model=ApplicationAutomationResponse)
async def auto_apply_to_job(
    request: ApplicationAutomationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Automatically apply to a job.

    Args:
        request: Automation request parameters

    Returns:
        Application automation response
    """
    if credentials.credentials != AUTOMATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid automation API key",
        )

    try:
        logger.info("Starting auto-apply for task: %s", request.task_id)

        # Get task from database
        db = next(get_db())
        task = (
            db.query(ApplicationTask)
            .filter(ApplicationTask.id == request.task_id)
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application task not found",
            )

        # Check if task belongs to current user
        if str(task.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this task",
            )

        # Set headless mode
        os.environ["HEADLESS"] = str(request.headless).lower()

        # Run automation
        result = await application_automation_service.run_application_task(task)

        logger.info("Auto-apply completed: %s", result)

        return ApplicationAutomationResponse(
            success=result["success"],
            task_id=request.task_id,
            status=result["status"],
            message=result["message"],
            submitted=result["submitted"],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.error("Error in auto-apply: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run auto-apply: {str(e)}",
        )


@router.post("/auto-apply-all")
async def auto_apply_all(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Automatically apply to all pending jobs for the current user.

    Returns:
        Dictionary with application results
    """
    if credentials.credentials != AUTOMATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid automation API key",
        )

    try:
        logger.info("Starting auto-apply-all for user: %s", current_user.id)

        db = next(get_db())
        tasks = (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.user_id == current_user.id,
                ApplicationTask.status == "queued",
            )
            .all()
        )

        results = []
        for task in tasks:
            try:
                result = await application_automation_service.run_application_task(task)
                results.append(
                    {
                        "task_id": str(task.id),
                        "job_id": str(task.job_id),
                        "status": result["status"],
                        "submitted": result["submitted"],
                    }
                )

            except Exception as e:
                logger.error("Failed to apply to task %s: %s", ('task.id', 'e'))
                results.append(
                    {
                        "task_id": str(task.id),
                        "job_id": str(task.job_id),
                        "status": "failed",
                        "submitted": False,
                        "error": str(e),
                    }
                )

        return {
            "success": True,
            "total": len(tasks),
            "processed": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error("Error in auto-apply-all: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run auto-apply-all: {str(e)}",
        )


@router.get("/tasks/pending")
async def get_pending_tasks(current_user: User = Depends(get_current_user)):
    """
    Get pending application tasks for the current user.

    Returns:
        List of pending application tasks
    """
    try:
        db = next(get_db())
        tasks = (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.user_id == current_user.id,
                ApplicationTask.status == "queued",
            )
            .all()
        )

        return {
            "success": True,
            "pending": len(tasks),
            "tasks": [
                {
                    "id": str(task.id),
                    "job_id": str(task.job_id),
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                for task in tasks
            ],
        }

    except Exception as e:
        logger.error("Error getting pending tasks: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending tasks: {str(e)}",
        )


@router.get("/tasks/history")
async def get_application_history(current_user: User = Depends(get_current_user)):
    """
    Get application history for the current user.

    Returns:
        List of all application tasks with status
    """
    try:
        db = next(get_db())
        tasks = (
            db.query(ApplicationTask)
            .filter(ApplicationTask.user_id == current_user.id)
            .order_by(ApplicationTask.created_at.desc())
            .all()
        )

        return {
            "success": True,
            "total": len(tasks),
            "tasks": [
                {
                    "id": str(task.id),
                    "job_id": str(task.job_id),
                    "status": task.status,
                    "submitted": task.status == "success",
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "last_error": task.last_error,
                }
                for task in tasks
            ],
        }

    except Exception as e:
        logger.error("Error getting application history: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application history: {str(e)}",
        )


@router.get("/stats")
async def get_automation_stats(current_user: User = Depends(get_current_user)):
    """
    Get automation statistics for the current user.

    Returns:
        Statistics about automation performance
    """
    try:
        db = next(get_db())
        tasks = (
            db.query(ApplicationTask)
            .filter(ApplicationTask.user_id == current_user.id)
            .all()
        )

        stats = {
            "total": len(tasks),
            "pending": 0,
            "in_progress": 0,
            "success": 0,
            "failed": 0,
            "cancelled": 0,
        }

        for task in tasks:
            stats[task.status] = stats.get(task.status, 0) + 1

        success_rate = (
            stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        )

        return {"success": True, "stats": stats, "success_rate": round(success_rate, 2)}

    except Exception as e:
        logger.error("Error getting automation stats: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get automation stats: {str(e)}",
        )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
    """
    Cancel a pending application task.

    Args:
        task_id: ID of the task to cancel

    Returns:
        Success message
    """
    try:
        logger.info("Cancelling task: %s", task_id)

        db = next(get_db())
        task = db.query(ApplicationTask).filter(ApplicationTask.id == task_id).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application task not found",
            )

        # Check if task belongs to current user
        if str(task.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this task",
            )

        if task.status != "queued" and task.status != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or in-progress tasks can be cancelled",
            )

        task.status = "cancelled"
        db.add(task)
        db.commit()

        logger.info("Task cancelled successfully: %s", task_id)

        return {"success": True, "message": "Task cancelled successfully"}

    except Exception as e:
        logger.error("Error cancelling task: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        )


@router.post("/cover-letter/generate", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest, current_user: User = Depends(get_current_user)
):
    """
    Generate a personalized cover letter for a job application.

    Args:
        request: Cover letter generation request

    Returns:
        Generated cover letter with metadata
    """
    try:
        logger.info("Generating cover letter for job %s by user %s" % (request.job_id, current_user.id)
        )

        # Get job and profile data
        db = next(get_db())
        job = db.query(Job).filter(Job.id == request.job_id).first()
        profile = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == current_user.id)
            .first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )

        # Convert profile to dictionary
        profile_dict = {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "skills": profile.skills or [],
            "work_experience": profile.work_experience or [],
            "education": profile.education or [],
        }

        # Generate cover letter
        result = await cover_letter_service.generate_cover_letter(
            job_description=job.description,
            profile=profile_dict,
            custom_instructions=request.custom_instructions,
        )

        return CoverLetterResponse(
            success=result["success"],
            cover_letter=result["cover_letter"],
            word_count=result["word_count"],
            error=result["error"],
            metadata=result["metadata"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating cover letter: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter: {str(e)}",
        )


@router.post("/cover-letter/regenerate", response_model=CoverLetterResponse)
async def regenerate_cover_letter(
    request: CoverLetterRegenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate a cover letter with feedback.

    Args:
        request: Cover letter regeneration request

    Returns:
        Regenerated cover letter with metadata
    """
    try:
        logger.info("Regenerating cover letter for job %s by user %s" % (request.job_id, current_user.id)
        )

        # Get job and profile data
        db = next(get_db())
        job = db.query(Job).filter(Job.id == request.job_id).first()
        profile = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == current_user.id)
            .first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )

        # Convert profile to dictionary
        profile_dict = {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "skills": profile.skills or [],
            "work_experience": profile.work_experience or [],
            "education": profile.education or [],
        }

        # Regenerate cover letter
        result = await cover_letter_service.regenerate_cover_letter(
            job_description=job.description,
            profile=profile_dict,
            previous_letter=request.previous_letter,
            feedback=request.feedback,
        )

        return CoverLetterResponse(
            success=result["success"],
            cover_letter=result["cover_letter"],
            word_count=result["word_count"],
            error=result["error"],
            metadata=result["metadata"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error regenerating cover letter: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate cover letter: {str(e)}",
        )


@router.get("/domains/{domain}/status")
async def get_domain_status(domain: str):
    """
    Get rate limiting and circuit breaker status for a domain.

    Args:
        domain: Domain name (e.g., boards.greenhouse.io)

    Returns:
        Domain status information
    """
    try:
        # Create a dummy URL for the domain
        dummy_url = f"https://{domain}/test"
        status = domain_service.get_domain_status(dummy_url)

        return {"success": True, "domain": domain, "status": status}

    except Exception as e:
        logger.error("Error getting domain status for %s: %s", ('domain', 'e'))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get domain status: {str(e)}",
        )


@router.get("/domains/status")
async def get_all_domains_status():
    """
    Get status for all configured domains.

    Returns:
        Status information for all domains
    """
    try:
        db = next(get_db())
        domains = db.query(Domain).all()

        domain_statuses = []
        for domain in domains:
            dummy_url = f"https://{domain.host}/test"
            status = domain_service.get_domain_status(dummy_url)
            domain_statuses.append(
                {
                    "host": domain.host,
                    "ats_type": domain.ats_type,
                    "last_status": domain.last_status,
                    "rate_limiting": status["rate_limit"],
                    "circuit_breaker": status["circuit_breaker"],
                }
            )

        return {"success": True, "domains": domain_statuses}

    except Exception as e:
        logger.error("Error getting all domains status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get domains status: {str(e)}",
        )


@router.post("/notifications/send")
async def send_notification(
    request: NotificationRequest, current_user: User = Depends(get_current_user)
):
    """
    Send a notification to the user about application status.

    This endpoint can be used to notify users of various application events
    like CAPTCHA detection, failures, rate limiting, etc.

    Args:
        request: Notification request details

    Returns:
        Success confirmation
    """
    try:
        logger.info("Sending %s notification for task %s to user %s" % (request.notification_type, request.task_id, current_user.id)
        )

        # Here you would integrate with a notification service (push notifications, email, etc.)
        # For now, we'll just log the notification and return success

        # In a real implementation, you might:
        # - Send push notifications via APNs
        # - Send emails via SendGrid/Mailgun
        # - Store notifications in a database for the mobile app to fetch

        notification_data = {
            "user_id": str(current_user.id),
            "task_id": request.task_id,
            "type": request.notification_type,
            "message": request.message,
            "metadata": request.metadata or {},
            "timestamp": "2026-01-25T00:00:00Z",
        }

        # Log notification (in production, you'd send it)
        logger.info("Notification queued: %s", notification_data)

        # TODO: Implement actual notification sending
        # await notification_service.send_push_notification(current_user.id, request.message)
        # await notification_service.send_email(current_user.email, subject, body)

        return {
            "success": True,
            "message": "Notification sent successfully",
            "notification": notification_data,
        }

    except Exception as e:
        logger.error("Error sending notification: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}",
        )


@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user), limit: int = Query(20, ge=1, le=100)
):
    """
    Get recent notifications for the current user.

    Args:
        limit: Maximum number of notifications to return

    Returns:
        List of recent notifications
    """
    try:
        # In a real implementation, you'd fetch from a notifications table
        # For now, return an empty list

        return {"success": True, "notifications": [], "total": 0}

    except Exception as e:
        logger.error("Error getting notifications: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}",
        )
