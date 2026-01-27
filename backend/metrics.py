"""
Prometheus metrics for JobSwipe API
"""

import time

from fastapi import Response
from prometheus_client import (REGISTRY, Counter, Gauge, Histogram, Summary,
                               generate_latest)

# ============================================================
# API Request Metrics (Existing)
# ============================================================
try:
    api_requests_total = REGISTRY._names_to_collectors["api_requests_total"]
except KeyError:
    api_requests_total = Counter(
        "api_requests_total",
        "Total number of API requests",
        ["method", "endpoint", "status_code"],
    )

try:
    api_request_duration = REGISTRY._names_to_collectors["api_request_duration_seconds"]
except KeyError:
    api_request_duration = Histogram(
        "api_request_duration_seconds",
        "API request duration in seconds",
        ["method", "endpoint"],
    )

# ============================================================
# Authentication Metrics
# ============================================================
try:
    auth_login_attempts_total = REGISTRY._names_to_collectors[
        "auth_login_attempts_total"
    ]
except KeyError:
    auth_login_attempts_total = Counter(
        "auth_login_attempts_total",
        "Total number of login attempts",
        [
            "provider",
            "status",
        ],  # provider: local, google, linkedin; status: success, failed
    )

try:
    auth_token_generations_total = REGISTRY._names_to_collectors[
        "auth_token_generations_total"
    ]
except KeyError:
    auth_token_generations_total = Counter(
        "auth_token_generations_total",
        "Total number of access tokens generated",
        ["token_type"],  # access, refresh
    )

try:
    auth_active_sessions = REGISTRY._names_to_collectors["auth_active_sessions"]
except KeyError:
    auth_active_sessions = Gauge(
        "auth_active_sessions", "Number of currently active user sessions"
    )

try:
    auth_mfa_verifications_total = REGISTRY._names_to_collectors[
        "auth_mfa_verifications_total"
    ]
except KeyError:
    auth_mfa_verifications_total = Counter(
        "auth_mfa_verifications_total",
        "Total number of MFA verifications",
        ["status"],  # success, failed
    )

# ============================================================
# User Metrics
# ============================================================
try:
    users_registered_total = REGISTRY._names_to_collectors["users_registered_total"]
except KeyError:
    users_registered_total = Counter(
        "users_registered_total",
        "Total number of users registered",
        ["provider"],  # local, google, linkedin
    )

try:
    users_active_daily = REGISTRY._names_to_collectors["users_active_daily"]
except KeyError:
    users_active_daily = Gauge(
        "users_active_daily", "Number of active users in the last 24 hours"
    )

try:
    users_online_current = REGISTRY._names_to_collectors["users_online_current"]
except KeyError:
    users_online_current = Gauge(
        "users_online_current", "Number of currently online users"
    )

# ============================================================
# Job Matching Metrics (Existing)
# ============================================================
try:
    job_matching_requests_total = REGISTRY._names_to_collectors[
        "job_matching_requests_total"
    ]
except KeyError:
    job_matching_requests_total = Counter(
        "job_matching_requests_total",
        "Total number of job matching requests",
        ["result"],  # success, error
    )

try:
    job_matching_duration = REGISTRY._names_to_collectors[
        "job_matching_duration_seconds"
    ]
except KeyError:
    job_matching_duration = Histogram(
        "job_matching_duration_seconds", "Job matching duration in seconds"
    )

try:
    jobs_matched_total = REGISTRY._names_to_collectors["jobs_matched_total"]
except KeyError:
    jobs_matched_total = Counter(
        "jobs_matched_total",
        "Total number of jobs matched",
        ["score_range"],  # 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0
    )

try:
    job_match_scores = REGISTRY._names_to_collectors["job_match_scores"]
except KeyError:
    job_match_scores = Summary(
        "job_match_scores",
        "Distribution of job match scores",
        ["category"],  # tech, healthcare, education, etc.
    )

try:
    embedding_generation_duration = REGISTRY._names_to_collectors[
        "embedding_generation_duration_seconds"
    ]
except KeyError:
    embedding_generation_duration = Histogram(
        "embedding_generation_duration_seconds",
        "Embedding generation duration in seconds",
        ["model"],  # sentence-transformers, openai
    )

try:
    embedding_cache_hits_total = REGISTRY._names_to_collectors[
        "embedding_cache_hits_total"
    ]
except KeyError:
    embedding_cache_hits_total = Counter(
        "embedding_cache_hits_total",
        "Total number of embedding cache hits",
        ["cache_type"],  # redis, local
    )

try:
    embedding_cache_misses_total = REGISTRY._names_to_collectors[
        "embedding_cache_misses_total"
    ]
except KeyError:
    embedding_cache_misses_total = Counter(
        "embedding_cache_misses_total",
        "Total number of embedding cache misses",
        ["cache_type"],  # redis, local
    )

# ============================================================
# Job Deduplication Metrics
# ============================================================
try:
    jobs_deduplicated_total = REGISTRY._names_to_collectors["jobs_deduplicated_total"]
except KeyError:
    jobs_deduplicated_total = Counter(
        "jobs_deduplicated_total",
        "Total number of duplicate jobs detected",
        ["source"],  # greenhouse, lever, rss, manual
    )

try:
    deduplication_similarity_scores = REGISTRY._names_to_collectors[
        "deduplication_similarity_scores"
    ]
except KeyError:
    deduplication_similarity_scores = Histogram(
        "deduplication_similarity_scores",
        "Distribution of job similarity scores for deduplication",
        buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
    )

# ============================================================
# Job Ingestion Metrics (Existing)
# ============================================================
try:
    jobs_ingested_total = REGISTRY._names_to_collectors["jobs_ingested_total"]
except KeyError:
    jobs_ingested_total = Counter(
        "jobs_ingested_total",
        "Total number of jobs ingested",
        ["source", "status"],  # greenhouse, lever, rss; success, error
    )

try:
    ingestion_duration = REGISTRY._names_to_collectors["ingestion_duration_seconds"]
except KeyError:
    ingestion_duration = Histogram(
        "ingestion_duration_seconds", "Job ingestion duration in seconds", ["source"]
    )

try:
    jobs_parsed_total = REGISTRY._names_to_collectors["jobs_parsed_total"]
except KeyError:
    jobs_parsed_total = Counter(
        "jobs_parsed_total",
        "Total number of jobs parsed",
        ["parser_type", "status"],  # greenhouse, lever, rss; success, error
    )

# ============================================================
# Application Metrics
# ============================================================
try:
    applications_submitted_total = REGISTRY._names_to_collectors[
        "applications_submitted_total"
    ]
except KeyError:
    applications_submitted_total = Counter(
        "applications_submitted_total",
        "Total number of job applications submitted",
        ["method", "status"],  # manual, auto; success, failed
    )

try:
    applications_in_progress = REGISTRY._names_to_collectors["applications_in_progress"]
except KeyError:
    applications_in_progress = Gauge(
        "applications_in_progress", "Number of applications currently in progress"
    )

try:
    application_automation_tasks_total = REGISTRY._names_to_collectors[
        "application_automation_tasks_total"
    ]
except KeyError:
    application_automation_tasks_total = Counter(
        "application_automation_tasks_total",
        "Total number of application automation tasks",
        ["status", "ats_type"],  # queued, running, success, failed
    )

try:
    application_automation_duration = REGISTRY._names_to_collectors[
        "application_automation_duration_seconds"
    ]
except KeyError:
    application_automation_duration = Histogram(
        "application_automation_duration_seconds",
        "Application automation task duration in seconds",
        ["ats_type"],
    )

# ============================================================
# Resume Parsing Metrics
# ============================================================
try:
    resume_uploads_total = REGISTRY._names_to_collectors["resume_uploads_total"]
except KeyError:
    resume_uploads_total = Counter(
        "resume_uploads_total",
        "Total number of resume uploads",
        ["file_type", "status"],  # pdf, docx, doc; success, failed
    )

try:
    resume_parsing_duration = REGISTRY._names_to_collectors[
        "resume_parsing_duration_seconds"
    ]
except KeyError:
    resume_parsing_duration = Histogram(
        "resume_parsing_duration_seconds",
        "Resume parsing duration in seconds",
        ["parser_type"],  # basic, enhanced, openai
    )

try:
    skills_extracted_total = REGISTRY._names_to_collectors["skills_extracted_total"]
except KeyError:
    skills_extracted_total = Counter(
        "skills_extracted_total", "Total number of skills extracted from resumes"
    )

try:
    experience_years_detected = REGISTRY._names_to_collectors[
        "experience_years_detected"
    ]
except KeyError:
    experience_years_detected = Histogram(
        "experience_years_detected",
        "Distribution of experience years detected from resumes",
        buckets=[0, 1, 3, 5, 10, 15, 20, 30],
    )

# ============================================================
# Notification Metrics
# ============================================================
try:
    notifications_sent_total = REGISTRY._names_to_collectors["notifications_sent_total"]
except KeyError:
    notifications_sent_total = Counter(
        "notifications_sent_total",
        "Total number of notifications sent",
        ["type", "channel"],  # type: match, application, deadline; channel: email, push
    )

try:
    notifications_failed_total = REGISTRY._names_to_collectors["notifications_failed_total"]
except KeyError:
    notifications_failed_total = Counter(
        "notifications_failed_total",
        "Total number of failed notifications",
        ["type", "channel", "error_type"],
    )

try:
    notification_delivery_duration = REGISTRY._names_to_collectors[
        "notification_delivery_duration_seconds"
    ]
except KeyError:
    notification_delivery_duration = Histogram(
        "notification_delivery_duration_seconds",
        "Notification delivery duration in seconds",
        ["channel"],  # email, push
    )

# ============================================================
# Analytics Metrics
# ============================================================
try:
    analytics_events_total = REGISTRY._names_to_collectors["analytics_events_total"]
except KeyError:
    analytics_events_total = Counter(
        "analytics_events_total",
        "Total number of analytics events tracked",
        ["event_type"],  # page_view, job_swipe, application_start, etc.
    )

try:
    analytics_query_duration = REGISTRY._names_to_collectors[
        "analytics_query_duration_seconds"
    ]
except KeyError:
    analytics_query_duration = Histogram(
        "analytics_query_duration_seconds",
        "Analytics query duration in seconds",
        ["report_type"],  # dashboard, trends, funnel
    )

# ============================================================
# Storage Metrics
# ============================================================
try:
    storage_uploads_total = REGISTRY._names_to_collectors["storage_uploads_total"]
except KeyError:
    storage_uploads_total = Counter(
        "storage_uploads_total",
        "Total number of file uploads",
        ["storage_type", "status"],  # s3, local; success, failed
    )

try:
    storage_bytes_uploaded = REGISTRY._names_to_collectors["storage_bytes_uploaded"]
except KeyError:
    storage_bytes_uploaded = Counter(
        "storage_bytes_uploaded",
        "Total bytes uploaded to storage",
        ["storage_type"],  # s3, local
    )

try:
    storage_bytes_downloaded = REGISTRY._names_to_collectors["storage_bytes_downloaded"]
except KeyError:
    storage_bytes_downloaded = Counter(
        "storage_bytes_downloaded",
        "Total bytes downloaded from storage",
        ["storage_type"],  # s3, local
    )

# ============================================================
# Database Metrics
# ============================================================
try:
    database_connections_active = REGISTRY._names_to_collectors[
        "database_connections_active"
    ]
except KeyError:
    database_connections_active = Gauge(
        "database_connections_active", "Number of active database connections"
    )

try:
    database_connections_idle = REGISTRY._names_to_collectors[
        "database_connections_idle"
    ]
except KeyError:
    database_connections_idle = Gauge(
        "database_connections_idle", "Number of idle database connections"
    )

try:
    database_query_duration = REGISTRY._names_to_collectors[
        "database_query_duration_seconds"
    ]
except KeyError:
    database_query_duration = Histogram(
        "database_query_duration_seconds",
        "Database query duration in seconds",
        ["query_type"],  # select, insert, update, delete
    )

try:
    database_errors_total = REGISTRY._names_to_collectors["database_errors_total"]
except KeyError:
    database_errors_total = Counter(
        "database_errors_total",
        "Total number of database errors",
        ["error_type"],  # connection, constraint, timeout, deadlock
    )

# ============================================================
# Redis Cache Metrics
# ============================================================
try:
    redis_connections_active = REGISTRY._names_to_collectors["redis_connections_active"]
except KeyError:
    redis_connections_active = Gauge(
        "redis_connections_active", "Number of active Redis connections"
    )

try:
    redis_operations_total = REGISTRY._names_to_collectors["redis_operations_total"]
except KeyError:
    redis_operations_total = Counter(
        "redis_operations_total",
        "Total number of Redis operations",
        ["operation", "result"],  # get, set, delete; hit, miss, error
    )

try:
    redis_operation_duration = REGISTRY._names_to_collectors[
        "redis_operation_duration_seconds"
    ]
except KeyError:
    redis_operation_duration = Histogram(
        "redis_operation_duration_seconds",
        "Redis operation duration in seconds",
        ["operation"],  # get, set, delete
    )

try:
    redis_memory_used = REGISTRY._names_to_collectors["redis_memory_used_bytes"]
except KeyError:
    redis_memory_used = Gauge("redis_memory_used_bytes", "Redis memory usage in bytes")

# ============================================================
# Celery/Background Task Metrics
# ============================================================
try:
    celery_tasks_total = REGISTRY._names_to_collectors["celery_tasks_total"]
except KeyError:
    celery_tasks_total = Counter(
        "celery_tasks_total",
        "Total number of Celery tasks",
        ["task_name", "status"],  # status: success, failure, retry
    )

try:
    celery_task_duration = REGISTRY._names_to_collectors["celery_task_duration_seconds"]
except KeyError:
    celery_task_duration = Histogram(
        "celery_task_duration_seconds", "Celery task duration in seconds", ["task_name"]
    )

try:
    celery_queue_length = REGISTRY._names_to_collectors["celery_queue_length"]
except KeyError:
    celery_queue_length = Gauge(
        "celery_queue_length",
        "Number of tasks in Celery queue",
        ["queue_name"],  # notifications, ingestion, analytics, cleanup
    )

try:
    celery_worker_count = REGISTRY._names_to_collectors["celery_worker_count"]
except KeyError:
    celery_worker_count = Gauge(
        "celery_worker_count", "Number of active Celery workers"
    )

# ============================================================
# OAuth2 Metrics
# ============================================================
try:
    oauth2_auth_requests_total = REGISTRY._names_to_collectors[
        "oauth2_auth_requests_total"
    ]
except KeyError:
    oauth2_auth_requests_total = Counter(
        "oauth2_auth_requests_total",
        "Total number of OAuth2 authorization requests",
        ["provider"],  # google, linkedin
    )

try:
    oauth2_token_exchanges_total = REGISTRY._names_to_collectors[
        "oauth2_token_exchanges_total"
    ]
except KeyError:
    oauth2_token_exchanges_total = Counter(
        "oauth2_token_exchanges_total",
        "Total number of OAuth2 token exchanges",
        ["provider", "status"],  # success, failed
    )

# ============================================================
# Error/Exception Metrics
# ============================================================
try:
    exceptions_total = REGISTRY._names_to_collectors["exceptions_total"]
except KeyError:
    exceptions_total = Counter(
        "exceptions_total",
        "Total number of exceptions",
        ["exception_type", "endpoint"],  # exception_type: ValueError, KeyError, etc.
    )

try:
    error_responses_total = REGISTRY._names_to_collectors["error_responses_total"]
except KeyError:
    error_responses_total = Counter(
        "error_responses_total",
        "Total number of HTTP error responses",
        ["status_code", "endpoint"],
    )

# ============================================================
# Health and Availability Metrics
# ============================================================
try:
    health_check_total = REGISTRY._names_to_collectors["health_check_total"]
except KeyError:
    health_check_total = Counter(
        "health_check_total",
        "Total number of health checks",
        ["status", "component"],  # component: database, redis, all
    )

try:
    service_uptime_seconds = REGISTRY._names_to_collectors["service_uptime_seconds"]
except KeyError:
    service_uptime_seconds = Gauge(
        "service_uptime_seconds", "Service uptime in seconds"
    )

try:
    service_restarts_total = REGISTRY._names_to_collectors["service_restarts_total"]
except KeyError:
    service_restarts_total = Counter(
        "service_restarts_total",
        "Total number of service restarts",
        ["reason"],  # crash, deployment, manual
    )

# ============================================================
# Rate Limiting Metrics
# ============================================================
try:
    rate_limit_hits_total = REGISTRY._names_to_collectors["rate_limit_hits_total"]
except KeyError:
    rate_limit_hits_total = Counter(
        "rate_limit_hits_total",
        "Total number of rate limit hits",
        ["endpoint", "limit_type"],  # per_ip, per_user, global
    )

# ============================================================
# File Validation Metrics
# ============================================================
try:
    file_validation_total = REGISTRY._names_to_collectors["file_validation_total"]
except KeyError:
    file_validation_total = Counter(
        "file_validation_total",
        "Total number of file validations",
        ["file_type", "status"],  # success, failed, rejected
    )

try:
    file_size_bytes = REGISTRY._names_to_collectors["file_size_bytes"]
except KeyError:
    file_size_bytes = Histogram(
        "file_size_bytes",
        "Distribution of uploaded file sizes",
        ["file_type"],  # pdf, docx, doc, image
        buckets=[1024, 10240, 102400, 1048576, 5242880, 10485760],  # 1KB to 10MB
    )

# ============================================================
# Middleware Performance Metrics
# ============================================================
try:
    compression_ratio = REGISTRY._names_to_collectors["compression_ratio"]
except KeyError:
    compression_ratio = Histogram(
        "compression_ratio", "Response compression ratio", ["algorithm"]  # gzip, brotli
    )

try:
    sanitization_duration = REGISTRY._names_to_collectors[
        "sanitization_duration_seconds"
    ]
except KeyError:
    sanitization_duration = Histogram(
        "sanitization_duration_seconds", "Input sanitization duration in seconds"
    )

    # ============================================================
    # Custom Business Metrics
    # ============================================================
    try:
        match_accuracy_average = REGISTRY._names_to_collectors["match_accuracy_average"]
    except KeyError:
        match_accuracy_average = Gauge(
            "match_accuracy_average",
            "Average match accuracy score (0-1)",
        )

    try:
        application_success_rate = REGISTRY._names_to_collectors["application_success_rate"]
    except KeyError:
        application_success_rate = Gauge(
            "application_success_rate",
            "Application success rate (0-1)",
        )

    try:
        user_engagement_score = REGISTRY._names_to_collectors["user_engagement_score"]
    except KeyError:
        user_engagement_score = Gauge(
            "user_engagement_score",
            "User engagement score (0-1)",
        )

    # ============================================================
    # Helper Functions
    # ============================================================
    """Convert score to range bucket"""
    if score < 0.2:
        return "0-0.2"
    elif score < 0.4:
        return "0.2-0.4"
    elif score < 0.6:
        return "0.4-0.6"
    elif score < 0.8:
        return "0.6-0.8"
    

    return "0.8-1.0"


async def metrics_endpoint():
"""Prometheus metrics endpoint"""
    return Response(media_type="text/plain; charset=utf-8", content=generate_latest())


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
                method=method, endpoint=path, status_code=str(status_code)
            ).inc()
            api_request_duration.labels(method=method, endpoint=path).observe(duration)
