"""
Jobs Router

Handles job-related operations including feed retrieval, job details, and interactions.
"""

import json
import logging
import os
from typing import List, Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.routers.auth import get_current_user
from db.database import get_db
from db.models import CandidateProfile, Job, User, UserJobInteraction
from services.matching import (get_job_matches_for_profile,
                                       get_personalized_jobs)

router = APIRouter()

logger = logging.getLogger(__name__)

# Redis client for caching
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True
)


class MatchMetadata(BaseModel):
    """Metadata for job match scoring"""

    bm25_score: float
    has_skill_match: bool
    has_location_match: bool


class JobMatch(BaseModel):
    """Response model for job match with score and metadata"""

    id: str
    title: str
    company: str
    location: Optional[str]
    snippet: Optional[str]
    score: float
    metadata: MatchMetadata
    apply_url: Optional[str]

    class Config:
        from_attributes = True


class JobCard(BaseModel):
    """Response model for job card data"""

    id: str
    title: str
    company: str
    location: Optional[str]
    snippet: Optional[str]
    score: float
    apply_url: Optional[str]

    class Config:
        from_attributes = True


class SwipeAction(BaseModel):
    """Request model for swipe action"""

    action: str  # "right" or "left"


@router.get("/matches", response_model=List[JobMatch])
async def get_job_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get matched jobs for the current user with detailed scoring.

    Args:
        limit: Number of matches to return (1-100, default: 20)
        offset: Offset for pagination (default: 0)
        min_score: Minimum score threshold (0.0-1.0, default: 0.0)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of job matches with scores and metadata
    """
    try:
        # Check cache first
        cache_key = f"matches:{current_user.id}:{limit}:{offset}:{min_score}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            cached_matches = json.loads(cached_result)
            return [JobMatch(**match) for match in cached_matches]

        # Get candidate profile
        profile = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )

        # Get job matches
        matches = await get_job_matches_for_profile(
            profile=profile, limit=limit, offset=offset, min_score=min_score, db=db
        )

        # Convert to JobMatch format
        job_matches = [
            JobMatch(
                id=str(match["job"].id),
                title=match["job"].title,
                company=match["job"].company,
                location=match["job"].location,
                snippet=(
                    match["job"].description[:200] + "..."
                    if len(match["job"].description) > 200
                    else match["job"].description
                ),
                score=match["score"],
                metadata=MatchMetadata(
                    bm25_score=match["metadata"]["bm25_score"],
                    has_skill_match=match["metadata"]["has_skill_match"],
                    has_location_match=match["metadata"]["has_location_match"],
                ),
                apply_url=match["job"].apply_url,
            )
            for match in matches
        ]

        # Cache the result
        redis_client.setex(
            cache_key, 300, json.dumps([match.dict() for match in job_matches])
        )

        return job_matches

    except Exception as e:
        logger.error("Error retrieving job matches for user %s: %s" % (current_user.id, str(e))
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job matches",
        )


@router.get("/feed", response_model=List[JobCard])
async def get_feed(
    cursor: Optional[str] = Query(None),
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get personalized job feed with cursor-based pagination.

    Args:
        cursor: Optional cursor for pagination
        page_size: Number of jobs to return per page (default: 20)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of job cards with swipe actions
    """
    try:
        # Check cache first (handle Redis connection failures gracefully)
        cache_key = f"feed:{current_user.id}:{cursor or 'none'}:{page_size}"
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                cached_cards = json.loads(cached_result)
                return [JobCard(**card) for card in cached_cards]
        except Exception as cache_error:
            logger.warning("Failed to read from cache: %s. Continuing to fetch fresh data." % (str(cache_error))
            )

        scored_jobs = await get_personalized_jobs(
            user_id=current_user.id, cursor=cursor, page_size=page_size, db=db
        )

        # Convert to JobCard format
        job_cards = [
            JobCard(
                id=str(job_data["job"].id),
                title=job_data["job"].title,
                company=job_data["job"].company,
                location=job_data["job"].location,
                snippet=(
                    job_data["job"].description[:200] + "..."
                    if len(job_data["job"].description) > 200
                    else job_data["job"].description
                ),
                score=job_data["score"],
                apply_url=job_data["job"].apply_url,
            )
            for job_data in scored_jobs
        ]

        # Cache the result (handle Redis connection failures gracefully)
        try:
            redis_client.setex(
                cache_key, 300, json.dumps([card.dict() for card in job_cards])
            )
        except Exception as cache_error:
            logger.warning("Failed to cache job feed: %s. Continuing without caching." % (str(cache_error))
            )

        return job_cards

    except Exception as e:
        logger.error("Error retrieving job feed for user %s: %s", ('current_user.id', 'str(e)'))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job feed",
        )


@router.get("/{job_id}", response_model=JobCard)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed job information.

    Args:
        job_id: Job identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Job card with detailed information
    """
    import uuid

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
        )

    job = db.query(Job).filter(Job.id == job_uuid).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return JobCard(
        id=str(job.id),
        title=job.title,
        company=job.company,
        location=job.location,
        snippet=job.description,
        score=0.85,
        apply_url=job.apply_url,
    )


@router.post("/{job_id}/swipe")
async def swipe_job(
    job_id: str,
    swipe_data: SwipeAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Record job swipe action and create application task if swiping right.

    Args:
        job_id: Job identifier
        swipe_data: Swipe action data (right or left)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Validate swipe action
    if swipe_data.action not in ["right", "left"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid swipe action. Must be 'right' or 'left'",
        )

    # Check if job exists
    import uuid

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
        )

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Check if interaction already exists
    existing_interaction = (
        db.query(UserJobInteraction)
        .filter(
            UserJobInteraction.user_id == current_user.id,
            UserJobInteraction.job_id == job_id,
        )
        .first()
    )

    if existing_interaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already interacted with this job",
        )

    # Create interaction record
    interaction = UserJobInteraction(
        user_id=current_user.id, job_id=job_id, action=swipe_data.action
    )

    db.add(interaction)
    db.commit()

    # If swiping right, create application task
    if swipe_data.action == "right":
        from services.application_service import create_application_task

        await create_application_task(
            user_id=str(current_user.id), job_id=str(job_id), db=db
        )

    return {
        "success": True,
        "message": f"Successfully swiped {swipe_data.action}",
        "job_id": job_id,
    }
