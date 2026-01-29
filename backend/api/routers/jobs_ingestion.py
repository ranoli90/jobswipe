"""
Jobs Ingestion Router

Provides endpoints for managing job ingestion operations.
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
from backend.services.job_ingestion_service import (  # noqa: F401
    ingest_jobs_once,
    job_ingestion_service,
)

router = APIRouter()
logger = logging.getLogger(__name__)

security = HTTPBearer()

# API key for ingestion operations (separate from user authentication)
INGESTION_API_KEY = settings.ingestion_api_key


class IngestionRequest(BaseModel):
    """Request model for job ingestion"""

    sources: List[str] = []
    interval_seconds: int = 3600


class IngestionResponse(BaseModel):
    """Response model for job ingestion"""

    success: bool
    message: str
    jobs_ingested: int
    jobs_processed: int
    failed: int


class JobIngestionStatus(BaseModel):
    """Response model for ingestion status"""

    is_running: bool
    last_run: str
    next_run: str
    total_jobs_ingested: int
    failed_jobs: int


@router.post("/sources/greenhouse/sync")
async def sync_greenhouse_board(
    board_token: str,
    incremental: bool = True,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Sync jobs from Greenhouse public board.

    Args:
        board_token: Greenhouse board token
        incremental: Whether to use incremental sync
        credentials: API key for authentication

    Returns:
        Sync response
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    logger.info("Syncing Greenhouse board: %s, incremental: %s", ('board_token', 'incremental'))

    try:
        from workers.ingestion.greenhouse import \
            sync_greenhouse_board as greenhouse_sync

        jobs = await greenhouse_sync(board_token, incremental)

        return {
            "success": True,
            "message": f"Successfully synced {len(jobs)} jobs from Greenhouse board {board_token}",
            "jobs_synced": len(jobs),
        }

    except Exception as e:
        logger.error("Error syncing Greenhouse board: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Greenhouse board: {str(e)}",
        )


@router.post("/sources/lever/sync")
async def sync_lever_postings(
    org_slug: str,
    incremental: bool = True,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Sync jobs from Lever public postings API.

    Args:
        org_slug: Lever organization slug
        incremental: Whether to use incremental sync
        credentials: API key for authentication

    Returns:
        Sync response
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    logger.info("Syncing Lever organization: %s, incremental: %s", ('org_slug', 'incremental'))

    try:
        from workers.ingestion.lever import \
            sync_lever_postings as lever_sync

        jobs = await lever_sync(org_slug, incremental)

        return {
            "success": True,
            "message": f"Successfully synced {len(jobs)} jobs from Lever organization {org_slug}",
            "jobs_synced": len(jobs),
        }

    except Exception as e:
        logger.error("Error syncing Lever organization: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Lever organization: {str(e)}",
        )


@router.post("/sources/rss/sync")
async def sync_rss_feed(
    feed_url: str, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Sync jobs from RSS feed.

    Args:
        feed_url: URL of the RSS feed
        credentials: API key for authentication

    Returns:
        Sync response
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    logger.info("Syncing RSS feed: %s", feed_url)

    try:
        from workers.ingestion.rss import sync_rss_feed as rss_sync

        jobs = await rss_sync(feed_url)

        return {
            "success": True,
            "message": f"Successfully synced {len(jobs)} jobs from RSS feed {feed_url}",
            "jobs_synced": len(jobs),
        }

    except Exception as e:
        logger.error("Error syncing RSS feed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync RSS feed: {str(e)}",
        )


@router.post("/ingest", response_model=IngestionResponse)
async def trigger_ingestion(
    request: IngestionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Trigger immediate job ingestion.

    Args:
        request: Ingestion configuration
        credentials: API key for authentication

    Returns:
        Ingestion response
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    logger.info("Triggering job ingestion with request: %s", request)

    try:
        jobs = await ingest_jobs_once()

        # Process jobs
        success_count = len(jobs)
        failed_count = 0

        # In a real implementation, we'd track actual success/failure

        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {len(jobs)} jobs",
            jobs_ingested=len(jobs),
            jobs_processed=success_count,
            failed=failed_count,
        )

    except Exception as e:
        logger.error("Error triggering ingestion: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger ingestion: {str(e)}",
        )


@router.get("/status", response_model=JobIngestionStatus)
async def get_ingestion_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Get current ingestion status.

    Args:
        credentials: API key for authentication

    Returns:
        Ingestion status
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    try:
        # In a real implementation, we'd track actual ingestion status
        # This is a placeholder for demo purposes
        return JobIngestionStatus(
            is_running=True,
            last_run="2026-01-25T10:30:00Z",
            next_run="2026-01-25T11:30:00Z",
            total_jobs_ingested=1234,
            failed_jobs=42,
        )

    except Exception as e:
        logger.error("Error getting ingestion status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ingestion status: {str(e)}",
        )


@router.post("/start-periodic")
async def start_periodic_ingestion(
    request: IngestionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Start periodic job ingestion.

    Args:
        request: Ingestion configuration
        credentials: API key for authentication

    Returns:
        Success message
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    logger.info("Starting periodic ingestion with interval: %s seconds" % (request.interval_seconds)
    )

    try:
        # In a real implementation, this would start a background task
        return {
            "success": True,
            "message": f"Periodic ingestion started with interval {request.interval_seconds} seconds",
        }

    except Exception as e:
        logger.error("Error starting periodic ingestion: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start periodic ingestion: {str(e)}",
        )


@router.post("/stop-periodic")
async def stop_periodic_ingestion(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Stop periodic job ingestion.

    Args:
        credentials: API key for authentication

    Returns:
        Success message
    """
    # Validate API key
    if credentials.credentials != INGESTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key"
        )

    logger.info("Stopping periodic ingestion")

    try:
        # In a real implementation, this would stop the background task
        return {"success": True, "message": "Periodic ingestion stopped"}

    except Exception as e:
        logger.error("Error stopping periodic ingestion: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop periodic ingestion: {str(e)}",
        )


@router.get("/sources")
async def get_ingestion_sources():
    """
    Get configured job sources.

    Returns:
        List of configured job sources
    """
    try:
        return {
            "sources": [
                {
                    "name": "Greenhouse",
                    "type": "greenhouse",
                    "url": "https://boards-api.greenhouse.io",
                },
                {"name": "Lever", "type": "lever", "url": "https://api.lever.co"},
            ]
        }

    except Exception as e:
        logger.error("Error getting ingestion sources: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ingestion sources: {str(e)}",
        )
