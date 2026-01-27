"""
RSS Feed Job Ingestion

Handles job ingestion from RSS feeds.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

import feedparser
import httpx
from pydantic import BaseModel

from backend.db.database import get_db
from backend.db.models import Job

logger = logging.getLogger(__name__)


class RSSJob(BaseModel):
    """RSS feed job model"""

    id: str
    title: str
    link: str
    description: Optional[str] = None
    published: Optional[datetime] = None
    source_url: str


async def fetch_rss_feed(feed_url: str) -> List[RSSJob]:
    """
    Fetch jobs from RSS feed.

    Args:
        feed_url: URL of the RSS feed

    Returns:
        List of RSSJob objects
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(feed_url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            jobs = []

            for entry in feed.entries:
                job = RSSJob(
                    id=entry.get("id", entry.link),
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    description=entry.get("summary", ""),
                    published=(
                        datetime(*entry.published_parsed[:6])
                        if hasattr(entry, "published_parsed")
                        else datetime.utcnow()
                    ),
                    source_url=feed_url,
                )
                jobs.append(job)

            logger.info(f"Fetched {len(jobs)} jobs from RSS feed: {feed_url}")
            return jobs

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error fetching RSS feed {feed_url}: {e.response.status_code} - {e.response.text}"
        )
        raise
    except Exception as e:
        logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
        raise


def normalize_rss_job(rss_job: RSSJob) -> dict:
    """
    Normalize RSS job data to internal format.

    Args:
        rss_job: RSSJob object

    Returns:
        Normalized job dictionary
    """
    # Extract company name from title or description if possible
    company = ""
    title = rss_job.title.strip()

    # Simple company extraction from common formats like "Job Title at Company"
    if " at " in title:
        company = title.split(" at ")[1]

    return {
        "source": "rss",
        "external_id": rss_job.id,
        "title": title,
        "company": company,
        "location": "",  # Usually not in RSS feed
        "description": rss_job.description,
        "raw_json": {
            "title": rss_job.title,
            "link": rss_job.link,
            "description": rss_job.description,
            "published": rss_job.published.isoformat() if rss_job.published else None,
            "source_url": rss_job.source_url,
        },
        "apply_url": rss_job.link,
    }


def update_or_create_job(rss_job: RSSJob, db) -> Job:
    """
    Update existing job or create new one.

    Args:
        rss_job: RSSJob object
        db: Database session

    Returns:
        Job object
    """
    normalized_job = normalize_rss_job(rss_job)

    # Check if job already exists
    existing_job = (
        db.query(Job)
        .filter(Job.source == "rss", Job.external_id == normalized_job["external_id"])
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
        existing_job.updated_at = datetime.utcnow()
        db.add(existing_job)
        logger.info(
            f"Updated RSS job: {normalized_job['title']} ({normalized_job['external_id']})"
        )
        return existing_job
    else:
        # Create new job
        new_job = Job(**normalized_job)
        db.add(new_job)
        logger.info(
            f"Created new RSS job: {normalized_job['title']} ({normalized_job['external_id']})"
        )
        return new_job


async def sync_rss_feed(feed_url: str) -> List[Job]:
    """
    Sync jobs from RSS feed.

    Args:
        feed_url: URL of the RSS feed

    Returns:
        List of synced jobs
    """
    db = next(get_db())
    try:
        jobs = await fetch_rss_feed(feed_url)
        synced_jobs = []

        for job in jobs:
            synced_job = update_or_create_job(job, db)
            synced_jobs.append(synced_job)

        db.commit()
        logger.info(
            f"Successfully synced {len(synced_jobs)} jobs from RSS feed {feed_url}"
        )
        return synced_jobs

    except Exception as e:
        db.rollback()
        logger.error(f"Error syncing RSS feed {feed_url}: {str(e)}")
        raise
    finally:
        db.close()
