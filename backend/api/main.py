#!/usr/bin/env python3
"""
JobSwipe API - Main Entry Point

FastAPI-based API for job search and application automation platform.
"""

import logging
import logging.config
import os
import uuid
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import redis
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter.exceptions import RateLimitExceeded
from pythonjsonlogger import jsonlogger

from backend.api.middleware.compression import add_compression_middleware
from backend.api.middleware.error_handling import add_error_handling_middleware
from backend.api.middleware.file_validation import \
    add_file_validation_middleware
from backend.api.middleware.input_sanitization import \
    InputSanitizationMiddleware
from backend.api.middleware.output_encoding import OutputEncodingMiddleware
from backend.api.routers import (analytics, application_automation,
                                 applications, auth, job_categorization,
                                 job_deduplication, jobs, jobs_ingestion,
                                 notifications, profile, api_keys)
from backend.config import Settings
from backend.db.database import get_db
from backend.metrics import MetricsMiddleware, metrics_endpoint
from backend.services.embedding_service import EmbeddingService
from backend.tracing import setup_tracing

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "logs/app.log")
log_max_size = int(os.getenv("LOG_MAX_SIZE", 10485760))  # 10MB
log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))

# Ensure log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s %(service)s",
        },
        "json_security": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s SECURITY %(levelname)s %(message)s %(ip)s %(user)s %(path)s %(request_id)s %(service)s",
        },
    },
    "handlers": {
        "console": {
            "level": log_level,
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": log_level,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": log_file,
            "maxBytes": log_max_size,
            "backupCount": log_backup_count,
        },
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json_security",
            "filename": "logs/security.log",
            "maxBytes": log_max_size,
            "backupCount": log_backup_count,
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": log_level,
            "propagate": True,
        },
        "security": {
            "handlers": ["security_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


class StructuredLoggingFilter(logging.Filter):
    """Add structured fields to log records"""

    def filter(self, record):
        record.service = "jobswipe-api"
        # Get request_id from thread local or context
        record.request_id = getattr(record, "request_id", "unknown")
        return True


# Add filter to root logger
logging.getLogger().addFilter(StructuredLoggingFilter())

logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


class CorrelationIdMiddleware:
    """Middleware to handle correlation IDs for distributed tracing"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict((k, v) for k, v in scope.get("headers", []))
        correlation_id = headers.get(b"x-correlation-id", uuid.uuid4().hex.encode())

        # Store in scope for use in spans
        scope["correlation_id"] = correlation_id.decode()

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = message.get("headers", []) + [
                    (b"x-correlation-id", correlation_id)
                ]
            await send(message)

        # Set request_id in logging context
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = correlation_id.decode()
            return record

        logging.setLogRecordFactory(record_factory)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            logging.setLogRecordFactory(old_factory)


app = FastAPI(
    title="JobSwipe API", version="1.0.0", max_request_size=10 * 1024 * 1024
)  # 10MB limit

settings = Settings()


# Setup rate limiting with Redis
@app.on_event("startup")
async def startup():
    # Validate environment configuration on startup
    logger.info("Validating environment configuration...")
    try:
        # Settings are already validated during instantiation, but we log success
        logger.info("Environment configuration validation successful")
        logger.info("Environment: %s", settings.environment)
        logger.info("Debug mode: %s", settings.debug)
    except Exception as e:
        logger.error("Environment configuration validation failed: %s", e)
        raise

    redis_instance = redis.from_url(
        settings.redis_url, encoding="utf8", decode_responses=True
    )
    await FastAPILimiter.init(redis_instance)


# Rate limiters
auth_limiter = RateLimiter(
    times=5,
    seconds=60,
    identifier=lambda request: request.client.host if request.client else "unknown",
)
api_limiter = RateLimiter(
    times=60,
    seconds=60,
    identifier=lambda request: getattr(
        request.state, "user_id", request.client.host if request.client else "unknown"
    ),
)
public_limiter = RateLimiter(
    times=100,
    seconds=60,
    identifier=lambda request: request.client.host if request.client else "unknown",
)


# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    client_ip = request.client.host if request.client else "unknown"
    user_id = (
        getattr(request.state, "user_id", "anonymous")
        if hasattr(request.state, "user_id")
        else "anonymous"
    )

    # Log rate limit violation
    security_logger.warning(
        "Rate limit exceeded",
        extra={
            "ip": client_ip,
            "user": user_id,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    # Calculate retry-after (assume 60 seconds for simplicity, or get from exc if available)
    retry_after = 60  # seconds

    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"},
        headers={"Retry-After": str(retry_after)},
    )


# Setup OpenTelemetry tracing
setup_tracing(app)

# CORS configuration - using settings from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)


# Security headers middleware
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Capture the original send to modify responses
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers
                message["headers"].append(
                    (b"content-security-policy", 
                     b"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:")
                )
                message["headers"].append(
                    (b"x-frame-options", b"DENY")
                )
                message["headers"].append(
                    (b"x-xss-protection", b"1; mode=block")
                )
                message["headers"].append(
                    (b"x-content-type-options", b"nosniff")
                )
                message["headers"].append(
                    (b"referrer-policy", b"strict-origin-when-cross-origin")
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(SecurityHeadersMiddleware)

# Input sanitization middleware
app.add_middleware(InputSanitizationMiddleware)

# Output encoding middleware
app.add_middleware(OutputEncodingMiddleware)

# Prometheus metrics middleware
app.add_middleware(MetricsMiddleware)

# Response compression
compression_type = os.getenv("COMPRESSION_TYPE", "gzip")
add_compression_middleware(app, compression_type=compression_type)

# Error handling middleware
include_traceback = os.getenv("DEBUG", "false").lower() == "true"
add_error_handling_middleware(app, include_traceback=include_traceback)

# File upload validation middleware
add_file_validation_middleware(app)

# Include routers with rate limiting
from fastapi import Depends

app.include_router(
    auth.router, prefix="/api/v1/auth", tags=["auth"], dependencies=[Depends(auth_limiter)]
)
app.include_router(
    profile.router,
    prefix="/api/v1/profile",
    tags=["profile"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(
    jobs.router, prefix="/api/v1/jobs", tags=["jobs"], dependencies=[Depends(api_limiter)]
)
app.include_router(
    applications.router,
    prefix="/api/v1/applications",
    tags=["applications"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(
    jobs_ingestion.router,
    prefix="/api/v1/ingestion",
    tags=["ingestion"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["analytics"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(
    application_automation.router,
    prefix="/api/v1/application-automation",
    tags=["application-automation"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(
    job_deduplication.router,
    prefix="/api/v1/deduplicate",
    tags=["deduplication"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(
    job_categorization.router,
    prefix="/api/v1/categorize",
    tags=["categorization"],
    dependencies=[Depends(api_limiter)],
)
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"], dependencies=[Depends(api_limiter)])
app.include_router(api_keys.router, prefix="/api/v1/admin/api-keys", tags=["API Keys"], dependencies=[Depends(api_limiter)])


# Global exception handler for error logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    client_ip = request.client.host if request.client else "unknown"
    user_id = (
        getattr(request.state, "user_id", "anonymous")
        if hasattr(request.state, "user_id")
        else "anonymous"
    )

    # Log security events for authentication/authorization failures
    if isinstance(exc, (ValueError, TypeError)) and "auth" in str(exc).lower():
        security_logger.warning(
            "Authentication failure",
            extra={"ip": client_ip, "user": user_id, "path": str(request.url.path)},
        )

    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/", dependencies=[Depends(public_limiter)])
async def root():
    """Root endpoint - health check"""
    return {"message": "Welcome to JobSwipe API"}


@app.get("/health", dependencies=[Depends(public_limiter)])
async def health_check():
    """Basic health check endpoint - service availability"""
    return {"status": "healthy", "service": "JobSwipe API", "version": "1.0.0"}


@app.get("/ready", ('exc', '"detail": "Internal server error"', '"service": "JobSwipe API", "version": "1.0.0", "status": "healthy"', '"status": "healthy", "service": "JobSwipe API", "version": "1.0.0"'))
async def readiness_check():
    """Readiness check endpoint - dependencies check"""
    health_status = {
        "status": "ready",
        "timestamp": datetime.datetime.now(timezone.utc).isoformat() + "Z",
        "services": {},
    }

    # Check database connectivity
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["services"]["database"] = "ready"
        db.close()
    except Exception as e:
        logger.error("Database readiness check failed: %s", exc_info=True)
        health_status["services"]["database"] = f"not ready: %s"
        health_status["status"] = "not ready"

    # Check Redis connectivity
    try:
        redis_url = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0", ('str(e)', 'str(e)'))
        if redis_url.startswith("redis://"):
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            health_status["services"]["redis"] = "ready"
        

        health_status["services"]["redis"] = "unknown"
    except Exception as e:
        logger.error("Redis readiness check failed: %s", exc_info=True)
        health_status["services"]["redis"] = f"not ready: %s"
        health_status["status"] = "not ready"

    # Check Ollama connectivity
    try:
        import httpx

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434", ('str(e)', 'str(e)'))
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                health_status["services"]["ollama"] = "ready"
            else:
                health_status["services"][
                    "ollama"
                ] = f"not ready: HTTP {response.status_code}"
                health_status["status"] = "not ready"
    except Exception as e:
        logger.error("Ollama readiness check failed: %s", exc_info=True)
        health_status["services"]["ollama"] = f"not ready: %s"
        health_status["status"] = "not ready"

    return health_status


@app.get("/metrics", ('str(e)', 'str(e)'))
async def get_metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()
