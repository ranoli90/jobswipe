#!/usr/bin/env python3
"""
Application Agent Worker

Background worker for running application automation tasks using Celery.
"""

import asyncio
import logging
import os

from celery import Celery
from services.application_service import run_application_task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Celery configuration (using Redis for both broker and result backend)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery instance
celery = Celery(
    "app_agent_worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
)


@celery.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    time_limit=300,
    soft_time_limit=240,
)
def application_task_worker(task_id):
    """
    Celery task for running application automation.

    Args:
        task_id: Application task ID
    """
    logger.info("Starting application task: %s", task_id)

    try:
        # Run the application task
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(run_application_task(task_id))

        if success:
            logger.info("Application task completed successfully: %s", task_id)
            return True
        

        logger.error("Application task failed: %s", task_id)
        raise Exception(f"Application task failed: {task_id}")

    except Exception as e:
        logger.error("Error in application task worker: %s", str(e))
        raise


@celery.task
def health_check():
    """Simple health check task"""
    logger.info("Health check task executed")
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info("Starting Application Agent Worker")
    logger.info("Broker URL: %s", CELERY_BROKER_URL)
    logger.info("Result Backend: %s", CELERY_RESULT_BACKEND)

    # Start worker
    celery.start()
