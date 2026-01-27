"""
Greenhouse Job Ingestion

Handles job ingestion from Greenhouse public boards API.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

import httpx
from pydantic import BaseModel

from backend.db.database import get_db
from backend.db.models import Job

logger = logging.getLogger(__name__)


class GreenhouseJob(BaseModel):
    """Greenhouse job API response model"""

    id: int
    title: str
    location: dict
    absolute_url: str
    updated_at: datetime
    content: Optional[str] = None


async def fetch_greenhouse_board(board_token: str) -> List[GreenhouseJob]:
    """
    Fetch jobs from Greenhouse public board API.

    Args:
        board_token: Greenhouse board token

    Returns:
        List of GreenhouseJob objects
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            jobs = data.get("jobs", [])

            return [
                GreenhouseJob(
                    id=job["id"],
                    title=job["title"],
                    location=job["location"],
                    absolute_url=job["absolute_url"],
                    updated_at=(
                        datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
                        if job.get("updated_at")
                        else datetime.now(timezone.utc)
                    ),
                    content=json.dumps(job),  # Store raw JSON
                )
                for job in jobs
            ]

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching Greenhouse board %s: %s - %s" % (board_token, e.response.status_code, e.response.text)
        )
        raise
    except Exception as e:
        logger.error("Error fetching Greenhouse board %s: %s", ('board_token', 'str(e)'))
        raise


def normalize_greenhouse_job(greenhouse_job: GreenhouseJob) -> dict:
    """
    Normalize Greenhouse job data to internal format.

    Args:
        greenhouse_job: GreenhouseJob object

    Returns:
        Normalized job dictionary
    """
    location_str = ""
    if greenhouse_job.location:
        location_parts = []
        if greenhouse_job.location.get("name"):
            location_parts.append(greenhouse_job.location["name"])
        if greenhouse_job.location.get("city"):
            location_parts.append(greenhouse_job.location["city"])
        if greenhouse_job.location.get("state"):
            location_parts.append(greenhouse_job.location["state"])
        if greenhouse_job.location.get("country"):
            location_parts.append(greenhouse_job.location["country"])

        location_str = ", ".join(location_parts)

    return {
        "source": "greenhouse",
        "external_id": str(greenhouse_job.id),
        "title": greenhouse_job.title,
        "company": "",  # Greenhouse API doesn't provide company name in board endpoint
        "location": location_str,
        "description": "",  # No detailed description in board API
        "raw_json": (
            json.loads(greenhouse_job.content) if greenhouse_job.content else {}
        ),
        "apply_url": greenhouse_job.absolute_url,
    }


def update_or_create_job(greenhouse_job: GreenhouseJob, db) -> Job:
    """
    Update existing job or create new one.

    Args:
        greenhouse_job: GreenhouseJob object
        db: Database session

    Returns:
        Job object
    """
    normalized_job = normalize_greenhouse_job(greenhouse_job)

    # Check if job already exists
    existing_job = (
        db.query(Job)
        .filter(
            Job.source == "greenhouse", Job.external_id == normalized_job["external_id"]
        )
        .first()
    )

    if existing_job:
        # Update existing job
        existing_job.title = normalized_job["title"]
        existing_job.company = normalized_job["company"]
        existing_job.location = normalized_job["location"]
        existing_job.description = normalized_job["description"]
        existing_job.raw_json = normalized_job["raw_json"]
        existing_job.apply_url = normalized_job["apply_url"]
        existing_job.updated_at = datetime.now(timezone.utc)
        db.add(existing_job)
        logger.info("Updated Greenhouse job: %s (%s)", normalized_job["title"], normalized_job["external_id"])
        return existing_job
    

    # Create new job
    new_job = Job(**normalized_job)
    db.add(new_job)
    logger.info("Created new Greenhouse job: %s (%s)", normalized_job["title"], normalized_job["external_id"])
    )
        return new_job


async def sync_greenhouse_board(
    board_token: str, incremental: bool = True
) -> List[Job]:
    """
    Sync jobs from Greenhouse public board.

    Args:
        board_token: Greenhouse board token
        incremental: Whether to use incremental sync

    Returns:
        List of synced jobs
    """
    db = next(get_db())
    try:
        jobs = await fetch_greenhouse_board(board_token)
        synced_jobs = []

        if incremental:
            # Get latest updated_at from existing jobs
            latest_updated = (
                db.query(Job.updated_at)
                .filter(
                    Job.source == "greenhouse",
                    Job.raw_json.contains({"board_token": board_token}),
                )
                .order_by(Job.updated_at.desc())
                .first()
            )

            if latest_updated:
                latest_updated = latest_updated[0]
                logger.info("Using incremental sync from %s", latest_updated)
                # Filter jobs updated after latest_updated
                jobs = [job for job in jobs if job.updated_at > latest_updated]

        for job in jobs:
            # Add board_token to raw_json for tracking
            job.content = json.dumps(
                {**json.loads(job.content), "board_token": board_token}
            )
            synced_job = update_or_create_job(job, db)
            synced_jobs.append(synced_job)

        db.commit()
        logger.info("Successfully synced %s jobs from Greenhouse board %s" % (len(synced_jobs), board_token)
        )
        return synced_jobs

    except Exception as e:
        db.rollback()
        logger.error("Error syncing Greenhouse board %s: %s", ('board_token', 'str(e)'))
        raise
    finally:
        db.close()
