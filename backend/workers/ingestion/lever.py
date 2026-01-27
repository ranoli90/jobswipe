"""
Lever Job Ingestion

Handles job ingestion from Lever public API and career pages.
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


class LeverJob(BaseModel):
    """Lever job API response model"""

    id: str
    text: str
    hostedUrl: str
    categories: dict
    createdAt: Optional[datetime] = None
    content: Optional[str] = None


async def fetch_lever_postings(org_slug: str) -> List[LeverJob]:
    """
    Fetch jobs from Lever public postings API.

    Args:
        org_slug: Lever organization slug

    Returns:
        List of LeverJob objects
    """
    url = f"https://api.lever.co/v0/postings/{org_slug}?mode=json"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

            jobs = response.json()

            return [
                LeverJob(
                    id=job["id"],
                    text=job["text"],
                    hostedUrl=job["hostedUrl"],
                    categories=job.get("categories", {}),
                    createdAt=(
                        datetime.fromtimestamp(job["createdAt"] / 1000)
                        if job.get("createdAt")
                        else datetime.now(timezone.utc)
                    ),
                    content=json.dumps(job),  # Store raw JSON
                )
                for job in jobs
            ]

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching Lever postings for %s: %s - %s" % (org_slug, e.response.status_code, e.response.text)
        )
        raise
    except Exception as e:
        logger.error("Error fetching Lever postings for %s: %s", ('org_slug', 'str(e)'))
        raise


def normalize_lever_job(lever_job: LeverJob) -> dict:
    """
    Normalize Lever job data to internal format.

    Args:
        lever_job: LeverJob object

    Returns:
        Normalized job dictionary
    """
    # Extract location from categories
    location = ""
    if lever_job.categories:
        location_parts = []
        if lever_job.categories.get("location"):
            location_parts.append(lever_job.categories["location"])

        location = ", ".join(location_parts)

    return {
        "source": "lever",
        "external_id": lever_job.id,
        "title": lever_job.text,
        "company": "",  # Company name typically in org slug or text
        "location": location,
        "description": "",  # No detailed description in postings API
        "raw_json": json.loads(lever_job.content) if lever_job.content else {},
        "apply_url": lever_job.hostedUrl,
    }


def update_or_create_job(lever_job: LeverJob, db) -> Job:
    """
    Update existing job or create new one.

    Args:
        lever_job: LeverJob object
        db: Database session

    Returns:
        Job object
    """
    normalized_job = normalize_lever_job(lever_job)

    # Check if job already exists
    existing_job = (
        db.query(Job)
        .filter(Job.source == "lever", Job.external_id == normalized_job["external_id"])
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
        logger.info("Updated Lever job: %s (%s)", normalized_job["title"], normalized_job["external_id"])
        return existing_job
    

    # Create new job
    new_job = Job(**normalized_job)
    db.add(new_job)
    logger.info("Created new Lever job: %s (%s)", normalized_job["title"], normalized_job["external_id"])
    )
        return new_job


async def sync_lever_postings(org_slug: str, incremental: bool = True) -> List[Job]:
    """
    Sync jobs from Lever public postings API.

    Args:
        org_slug: Lever organization slug
        incremental: Whether to use incremental sync

    Returns:
        List of synced jobs
    """
    db = next(get_db())
    try:
        jobs = await fetch_lever_postings(org_slug)
        synced_jobs = []

        if incremental:
            # Get latest updated_at from existing jobs
            latest_updated = (
                db.query(Job.updated_at)
                .filter(
                    Job.source == "lever", Job.raw_json.contains({"org_slug": org_slug})
                )
                .order_by(Job.updated_at.desc())
                .first()
            )

            if latest_updated:
                latest_updated = latest_updated[0]
                logger.info("Using incremental sync from %s", latest_updated)
                # Filter jobs updated after latest_updated
                jobs = [job for job in jobs if job.createdAt > latest_updated]

        for job in jobs:
            # Add org_slug to raw_json for tracking
            job.content = json.dumps({**json.loads(job.content), "org_slug": org_slug})
            synced_job = update_or_create_job(job, db)
            synced_jobs.append(synced_job)

        db.commit()
        logger.info("Successfully synced %s jobs from Lever organization %s" % (len(synced_jobs), org_slug)
        )
        return synced_jobs

    except Exception as e:
        db.rollback()
        logger.error("Error syncing Lever organization %s: %s", ('org_slug', 'str(e)'))
        raise
    finally:
        db.close()
