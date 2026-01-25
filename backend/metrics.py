"""
Prometheus metrics for JobSwipe API
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from fastapi import Response
import time

# API Metrics
try:
    api_requests_total = REGISTRY._names_to_collectors['api_requests_total']
except KeyError:
    api_requests_total = Counter(
        'api_requests_total',
        'Total number of API requests',
        ['method', 'endpoint', 'status_code']
    )

try:
    api_request_duration = REGISTRY._names_to_collectors['api_request_duration_seconds']
except KeyError:
    api_request_duration = Histogram(
        'api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint']
    )

# Job Matching Metrics
try:
    job_matching_requests_total = REGISTRY._names_to_collectors['job_matching_requests_total']
except KeyError:
    job_matching_requests_total = Counter(
        'job_matching_requests_total',
        'Total number of job matching requests',
        ['result']  # success, error
    )

try:
    job_matching_duration = REGISTRY._names_to_collectors['job_matching_duration_seconds']
except KeyError:
    job_matching_duration = Histogram(
        'job_matching_duration_seconds',
        'Job matching duration in seconds'
    )

try:
    jobs_matched_total = REGISTRY._names_to_collectors['jobs_matched_total']
except KeyError:
    jobs_matched_total = Counter(
        'jobs_matched_total',
        'Total number of jobs matched',
        ['score_range']  # 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0
    )

# Application Automation Metrics
try:
    application_tasks_total = REGISTRY._names_to_collectors['application_tasks_total']
except KeyError:
    application_tasks_total = Counter(
        'application_tasks_total',
        'Total number of application tasks',
        ['status', 'ats_type']  # queued, running, success, failed
    )

try:
    application_task_duration = REGISTRY._names_to_collectors['application_task_duration_seconds']
except KeyError:
    application_task_duration = Histogram(
        'application_task_duration_seconds',
        'Application task duration in seconds',
        ['ats_type']
    )

# Ingestion Metrics
try:
    jobs_ingested_total = REGISTRY._names_to_collectors['jobs_ingested_total']
except KeyError:
    jobs_ingested_total = Counter(
        'jobs_ingested_total',
        'Total number of jobs ingested',
        ['source', 'status']  # greenhouse, lever, rss; success, error
    )

try:
    ingestion_duration = REGISTRY._names_to_collectors['ingestion_duration_seconds']
except KeyError:
    ingestion_duration = Histogram(
        'ingestion_duration_seconds',
        'Job ingestion duration in seconds',
        ['source']
    )

# System Metrics
try:
    active_connections = REGISTRY._names_to_collectors['active_connections']
except KeyError:
    active_connections = Gauge(
        'active_connections',
        'Number of active connections'
    )

try:
    database_connections = REGISTRY._names_to_collectors['database_connections_active']
except KeyError:
    database_connections = Gauge(
        'database_connections_active',
        'Number of active database connections'
    )

try:
    redis_connections = REGISTRY._names_to_collectors['redis_connections_active']
except KeyError:
    redis_connections = Gauge(
        'redis_connections_active',
        'Number of active Redis connections'
    )


def get_metrics_score_range(score: float) -> str:
    """Convert score to range bucket"""
    if score < 0.2:
        return "0-0.2"
    elif score < 0.4:
        return "0.2-0.4"
    elif score < 0.6:
        return "0.4-0.6"
    elif score < 0.8:
        return "0.6-0.8"
    else:
        return "0.8-1.0"


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(
        media_type="text/plain; charset=utf-8",
        content=generate_latest()
    )


class MetricsMiddleware:
    """FastAPI middleware for collecting metrics"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope["method"]
        path = scope["path"]

        # Create response wrapper to capture status code
        response_started = False
        status_code = 200

        async def wrapped_send(message):
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
            await send(message)

        await self.app(scope, receive, wrapped_send)

        if response_started:
            duration = time.time() - start_time
            api_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=str(status_code)
            ).inc()
            api_request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)