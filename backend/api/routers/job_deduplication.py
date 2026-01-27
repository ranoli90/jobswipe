"""
Job Deduplication Router

Provides endpoints for managing job deduplication operations.
"""

import logging
import os
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.api.routers.auth import get_current_user
from backend.config import settings
from backend.db.models import User
from backend.services.job_deduplication import (JobDeduplicationService,
                                                find_duplicates_in_db,
                                                remove_duplicates)

router = APIRouter(prefix="/api/deduplicate", tags=["deduplication"])
logger = logging.getLogger(__name__)

security = HTTPBearer()

# API key for deduplication operations (separate from user authentication)
DEDUPLICATION_API_KEY = settings.deduplication_api_key

deduplication_service = JobDeduplicationService()


class DeduplicationResponse(BaseModel):
    """Response model for deduplication operations"""

    success: bool
    message: str
    duplicate_groups_found: int
    duplicates_removed: int
    unique_jobs_count: int


class DuplicateGroup(BaseModel):
    """Response model for duplicate group"""

    main_job: Dict
    duplicates: List[Dict]


@router.get("/find")
async def find_duplicates(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Find duplicate jobs in the database.

    Args:
        credentials: API key for authentication

    Returns:
        List of duplicate groups
    """
    # Validate API key
    if credentials.credentials != DEDUPLICATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid deduplication API key",
        )

    logger.info("Finding duplicate jobs")

    try:
        duplicate_groups = find_duplicates_in_db()

        # Convert to response format
        response_groups = []
        for group in duplicate_groups:
            main_job = {
                "id": str(group[0][0].id),
                "title": group[0][0].title,
                "company": group[0][0].company,
                "source": group[0][0].source,
                "similarity": group[0][1],
            }

            duplicates = []
            for job, score in group[1:]:
                duplicates.append(
                    {
                        "id": str(job.id),
                        "title": job.title,
                        "company": job.company,
                        "source": job.source,
                        "similarity": score,
                    }
                )

            response_groups.append({"main_job": main_job, "duplicates": duplicates})

        return {
            "success": True,
            "message": f"Found {len(duplicate_groups)} duplicate groups",
            "duplicate_groups": response_groups,
        }

    except Exception as e:
        logger.error("Error finding duplicates: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find duplicates: {str(e)}",
        )


@router.post("/remove")
async def remove_duplicates_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Remove duplicate jobs from the database.

    Args:
        credentials: API key for authentication

    Returns:
        Deduplication response
    """
    # Validate API key
    if credentials.credentials != DEDUPLICATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid deduplication API key",
        )

    logger.info("Removing duplicate jobs")

    try:
        duplicate_groups = find_duplicates_in_db()
        removed_count = remove_duplicates(duplicate_groups)

        return {
            "success": True,
            "message": f"Removed {removed_count} duplicate jobs from {len(duplicate_groups)} groups",
            "duplicate_groups_found": len(duplicate_groups),
            "duplicates_removed": removed_count,
        }

    except Exception as e:
        logger.error("Error removing duplicates: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove duplicates: {str(e)}",
        )


@router.post("/run")
async def run_deduplication(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Run complete deduplication process.

    Args:
        credentials: API key for authentication

    Returns:
        Deduplication response
    """
    # Validate API key
    if credentials.credentials != DEDUPLICATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid deduplication API key",
        )

    logger.info("Running deduplication process")

    try:
        removed_count, duplicate_groups = deduplication_service.deduplicate()

        return {
            "success": True,
            "message": f"Removed {removed_count} duplicate jobs from {len(duplicate_groups)} groups",
            "duplicate_groups_found": len(duplicate_groups),
            "duplicates_removed": removed_count,
        }

    except Exception as e:
        logger.error("Error running deduplication: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run deduplication: {str(e)}",
        )
