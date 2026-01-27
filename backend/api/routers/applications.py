"""
Applications Router

Handles job application operations including task creation and status tracking.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.routers.auth import get_current_user
from backend.db.database import get_db
from backend.db.models import ApplicationAuditLog, ApplicationTask, User
from backend.services.application_service import (cancel_application,
                                                  create_application_task,
                                                  get_application_status)

router = APIRouter()

logger = logging.getLogger(__name__)


class ApplicationTaskResponse(BaseModel):
    """Response model for application task"""

    id: str
    job_id: str
    status: str
    attempt_count: int
    last_error: str
    assigned_worker: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ApplicationAuditLogResponse(BaseModel):
    """Response model for application audit log"""

    id: str
    step: str
    payload: dict
    artifacts: dict
    timestamp: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, audit_log):
        obj = super().from_orm(audit_log)
        # Add success field based on step type
        obj.success = not audit_log.step.lower().contains("error")
        return obj


class CreateApplicationRequest(BaseModel):
    """Request model for creating application"""

    job_id: str


@router.post("/", response_model=ApplicationTaskResponse)
async def create_application(
    request: CreateApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create application task for a job.

    Args:
        request: Application creation request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created application task
    """
    try:
        task = await create_application_task(
            user_id=str(current_user.id), job_id=request.job_id, db=db
        )

        return ApplicationTaskResponse.from_orm(task)

    except Exception as e:
        logger.error("Error creating application for user %s: %s", ('current_user.id', 'str(e)'))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}",
        )


@router.get("/", response_model=List[ApplicationTaskResponse])
async def get_applications(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get all applications for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of application tasks
    """
    applications = (
        db.query(ApplicationTask)
        .filter(ApplicationTask.user_id == current_user.id)
        .all()
    )

    return [ApplicationTaskResponse.from_orm(app) for app in applications]


@router.get("/{job_id}/status", response_model=ApplicationTaskResponse)
async def get_application_status_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get application status for a specific job.

    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Application task status
    """
    task = get_application_status(user_id=str(current_user.id), job_id=job_id, db=db)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )

    return ApplicationTaskResponse.from_orm(task)


@router.get("/{job_id}/audit", response_model=List[ApplicationAuditLogResponse])
async def get_application_audit(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get application audit log for a specific job.

    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Application audit log entries
    """
    # Get application task first
    task = (
        db.query(ApplicationTask)
        .filter(
            ApplicationTask.user_id == current_user.id, ApplicationTask.job_id == job_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )

    # Get audit logs
    audit_logs = (
        db.query(ApplicationAuditLog)
        .filter(ApplicationAuditLog.task_id == task.id)
        .order_by(ApplicationAuditLog.timestamp)
        .all()
    )

    return [ApplicationAuditLogResponse.from_orm(log) for log in audit_logs]


@router.post("/{job_id}/cancel")
async def cancel_application_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel application for a job.

    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    try:
        cancelled = cancel_application(
            user_id=str(current_user.id), job_id=job_id, db=db
        )

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        return {"success": True, "message": "Application cancelled successfully"}

    except Exception as e:
        logger.error(
            f"Error cancelling application for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel application: {str(e)}",
        )
