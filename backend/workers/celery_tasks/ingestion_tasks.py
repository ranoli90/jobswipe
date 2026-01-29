"""
Ingestion Background Tasks

Celery tasks for handling job data ingestion and processing.
"""

import logging
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import Job, JobSource
from services.embedding_service import EmbeddingService
from services.job_ingestion_service import job_ingestion_service
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, time_limit=300)
def ingest_jobs_from_source(self, source_name: str):
    """
    Ingest jobs from a specific source.

    Args:
        source_name: Name of the source (e.g., 'greenhouse', 'lever', 'rss')
    """
    import asyncio
    db = next(get_db())
    jobs_ingested = 0

    try:
        logger.info("Starting job ingestion from %s", source_name)

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if source_name == "greenhouse":
                jobs = loop.run_until_complete(job_ingestion_service.fetch_greenhouse_jobs())
            elif source_name == "lever":
                jobs = loop.run_until_complete(job_ingestion_service.fetch_lever_jobs())
            elif source_name == "rss":
                jobs = loop.run_until_complete(job_ingestion_service.fetch_rss_jobs())
            else:
                logger.error("Unknown source: %s", source_name)
                return {"status": "failed", "reason": "Unknown source"}
        finally:
            loop.close()

        for job_data in jobs:
            try:
                # Check if job already exists
                existing = (
                    db.query(Job)
                    .filter(
                        Job.external_id == job_data.get("external_id"),
                        Job.source == source_name,
                    )
                    .first()
                )

                if existing:
                    logger.debug("Job %s already exists, skipping", job_data.get("external_id"))
                    continue

                # Create new job
                job = Job(
                    title=job_data.get("title"),
                    company=job_data.get("company"),
                    description=job_data.get("description"),
                    location=job_data.get("location"),
                    source=source_name,
                    external_id=job_data.get("external_id"),
                    apply_url=job_data.get("apply_url"),
                    salary_range=job_data.get("salary_range"),
                    job_type=job_data.get("job_type"),
                    experience_level=job_data.get("experience_level"),
                    skills=job_data.get("skills", []),
                    remote_allowed=job_data.get("remote_allowed", False),
                )
                db.add(job)
                jobs_ingested += 1

            except Exception as e:
                logger.error("Error processing job: %s", e)
                continue

        db.commit()
        logger.info("Ingested %s jobs from %s", ('jobs_ingested', 'source_name'))
        return {"status": "success", "jobs_ingested": jobs_ingested}

    except Exception as e:
        logger.error("Failed to ingest jobs from %s: %s", ('source_name', 'e'))
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_job_embedding(self, job_id: str):
    """
    Generate and cache embedding for a job.

    Args:
        job_id: Job ID to process
    """
    import asyncio
    db = next(get_db())

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.warning("Job %s not found for embedding", job_id)
            return {"status": "failed", "reason": "Job not found"}

        # Generate embedding
        if EmbeddingService.is_available():
            description = job.description or ""
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                embedding = loop.run_until_complete(
                    EmbeddingService.generate_job_embedding(description)
                )

                # Store embedding in cache
                from services.embedding_cache import EmbeddingCache

                cache = EmbeddingCache()
                loop.run_until_complete(cache.set_embedding(f"job:{job_id}", embedding))

                logger.info("Generated embedding for job %s", job_id)
                return {"status": "success", "job_id": job_id}
            finally:
                loop.close()
        

        logger.warning("Embedding service not available")
        return {"status": "skipped", "reason": "Service unavailable"}

    except Exception as e:
        logger.error("Failed to process embedding for job %s: %s", ('job_id', 'e'))
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task
def refresh_job_embeddings():
    """
    Refresh embeddings for recently added jobs.

    Returns:
        Number of embeddings processed
    """
    db = next(get_db())
    processed = 0

    try:
        # Get jobs without embeddings (last 24 hours)
        from datetime import timedelta

        yesterday = datetime.now(timezone.utc) - timedelta(days=1)

        jobs = db.query(Job).filter(Job.created_at >= yesterday).all()

        for job in jobs:
            process_job_embedding.delay(job.id)
            processed += 1

        logger.info("Queued %s jobs for embedding refresh", processed)
        return processed

    except Exception as e:
        logger.error("Error refreshing job embeddings: %s", e)
        return 0
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def deduplicate_jobs(self, batch_size: int = 1000):
    """
    Run job deduplication on recent jobs.

    Args:
        batch_size: Number of jobs to process per batch
    """
    import asyncio
    db = next(get_db())

    try:
        from datetime import timedelta

        from services.job_deduplication import \
            job_deduplication_service

        # Get recent jobs for deduplication
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        jobs = db.query(Job).filter(Job.created_at >= week_ago).limit(batch_size).all()

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            duplicates_found = 0
            for job in jobs:
                duplicates = loop.run_until_complete(
                    job_deduplication_service.find_duplicates(job)
                )
                if duplicates:
                    duplicates_found += len(duplicates)
                    # Mark duplicates for review
                    for dup in duplicates:
                        dup.is_duplicate = True
                        dup.duplicate_of = job.id

            db.commit()
            logger.info("Found %s potential duplicates", duplicates_found)
            return {"status": "success", "duplicates_found": duplicates_found}
        finally:
            loop.close()

    except Exception as e:
        logger.error("Error during job deduplication: %s", e)
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task
def sync_all_sources():
    """
    Trigger job ingestion from all configured sources.

    Returns:
        Summary of ingestion results
    """
    # Define ingestion sources as a constant
    INGESTION_SOURCES = ["greenhouse", "lever", "rss"]
    results = {}
    sources = INGESTION_SOURCES

    for source in sources:
        task = ingest_jobs_from_source.delay(source)
        results[source] = task.id

    logger.info("Triggered ingestion for sources: %s", list(results.keys()))
    return {"status": "triggered", "tasks": results}


@celery_app.task
def cleanup_expired_jobs(days: int = 30):
    """
    Mark jobs older than specified days as expired.

    Args:
        days: Number of days after which jobs expire

    Returns:
        Number of jobs marked as expired
    """
    db = next(get_db())
    expired = 0

    try:
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Mark jobs as expired
        result = (
            db.query(Job)
            .filter(Job.created_at < cutoff, Job.is_active is True)
            .update({"is_active": False})
        )

        db.commit()
        expired = result
        logger.info("Marked %s jobs as expired", expired)
        return expired

    except Exception as e:
        logger.error("Error marking expired jobs: %s", e)
        db.rollback()
        return 0
    finally:
        db.close()
