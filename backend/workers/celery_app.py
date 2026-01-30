"""
Celery Application Configuration

Background task queue for async job processing using Redis as broker.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Setup tracing
try:
    from backend.tracing import setup_tracing
except ImportError:
    from tracing import setup_tracing

# Configure Celery to use Redis as broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "jobswipe",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.workers.celery_tasks.notification_tasks",
        "backend.workers.celery_tasks.ingestion_tasks",
        "backend.workers.celery_tasks.analytics_tasks",
        "backend.workers.celery_tasks.cleanup_tasks",
    ],
)

# Setup OpenTelemetry tracing
setup_tracing(celery_app=celery_app)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=60 * 60 * 24,  # Results expire after 24 hours
    task_routes={
        "backend.workers.celery_tasks.notification_tasks.*": {"queue": "notifications"},
        "backend.workers.celery_tasks.ingestion_tasks.*": {"queue": "ingestion"},
        "backend.workers.celery_tasks.analytics_tasks.*": {"queue": "analytics"},
        "backend.workers.celery_tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens-daily": {
        "task": "backend.workers.celery_tasks.cleanup_tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM UTC
    },
    "cleanup-old-sessions-daily": {
        "task": "backend.workers.celery_tasks.cleanup_tasks.cleanup_old_sessions",
        "schedule": crontab(hour=3, minute=0),  # Run daily at 3 AM UTC
    },
    "send-daily-digest-emails": {
        "task": "backend.workers.celery_tasks.notification_tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),  # Run daily at 8 AM UTC
    },
    "refresh-job-embeddings-hourly": {
        "task": "backend.workers.celery_tasks.ingestion_tasks.refresh_job_embeddings",
        "schedule": crontab(minute=0),  # Run every hour
    },
    "generate-analytics-snapshots-hourly": {
        "task": "backend.workers.celery_tasks.analytics_tasks.generate_hourly_snapshot",
        "schedule": crontab(minute=5),  # Run every hour at 5 minutes past
    },
}

if __name__ == "__main__":
    celery_app.start()
