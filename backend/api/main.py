#!/usr/bin/env python3
"""
JobSwipe API - Main Entry Point

FastAPI-based API for job search and application automation platform.
"""

import logging
import logging.config
import os
import sys
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
from pythonjsonlogger import jsonlogger

# Try to import settings with proper error handling
try:
    from config import Settings
    settings = Settings()
except Exception as e:
    # Log to stderr before logging is configured
    print(f"CRITICAL ERROR: Failed to load settings: {e}", file=sys.stderr)
    print("This usually means required environment variables are missing.", file=sys.stderr)
    print("Required variables: DATABASE_URL, SECRET_KEY, ENCRYPTION_PASSWORD, ENCRYPTION_SALT, OAUTH_STATE_SECRET", file=sys.stderr)
    sys.exit(1)

from api.middleware.compression import add_compression_middleware
from api.middleware.error_handling import add_error_handling_middleware
from api.middleware.file_validation import \
    add_file_validation_middleware
from api.middleware.input_sanitization import \
    InputSanitizationMiddleware
from api.middleware.output_encoding import OutputEncodingMiddleware
from api.routers import (analytics, application_automation,
                         applications, auth, job_categorization,
                         job_deduplication, jobs, jobs_ingestion,
                         notifications, profile, api_keys)
from db.database import get_db, engine
from metrics import MetricsMiddleware, metrics_endpoint
from services.embedding_service import EmbeddingService
from tracing import setup_tracing

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "logs/app.log")
log_max_size = int(os.getenv("LOG_MAX_SIZE", 10485760))  # 10MB
log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))

# Ensure log directory exists
try:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create log directory: {e}", file=sys.stderr)
    # Fallback to stdout only logging
    log_file = "/dev/null"

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
            "handlers": ["console", "file"] if log_file != "/dev/null" else ["console"],
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


# Setup rate limiting with Redis
@app.on_event("startup")
async def startup():
    global redis_instance
    redis_instance = None
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

    # Initialize Redis with error handling
    try:
        redis_instance = redis.from_url(
            settings.redis_url, encoding="utf8", decode_responses=True
        )
        await FastAPILimiter.init(redis_instance)
        logger.info("Redis rate limiter initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Redis rate limiter: %s", e)
        logger.warning("Continuing without rate limiting - Redis unavailable")
        # Don't raise - allow app to start without Redis


@app.on_event("shutdown")
async def shutdown():
    global redis_instance
    if redis_instance:
        await redis_instance.close()
        logger.info("Redis connection closed gracefully")
    engine.dispose()
    logger.info("Database engine disposed gracefully")
    logger.info("Application shutdown complete")


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
@app.exception_handler(HTTPException)
async def rate_limit_exceeded_handler(request: Request, exc: HTTPException):
    if exc.status_code == 429:
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
    # For other HTTPExceptions, re-raise them
    raise exc


# Setup OpenTelemetry tracing
try:
    setup_tracing(app)
    logger.info("OpenTelemetry tracing initialized")
except Exception as e:
    logger.warning("Failed to initialize tracing: %s", e)

# CORS configuration - using settings from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Add security middleware
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(OutputEncodingMiddleware)

# Add compression middleware
add_compression_middleware(app)

# Add file validation middleware
add_file_validation_middleware(app)

# Add error handling middleware
add_error_handling_middleware(app)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)


# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1", tags=["applications"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(
    application_automation.router, prefix="/api/v1", tags=["application_automation"]
)
app.include_router(job_deduplication.router, prefix="/api/v1", tags=["deduplication"])
app.include_router(job_categorization.router, prefix="/api/v1", tags=["categorization"])
app.include_router(jobs_ingestion.router, prefix="/api/v1", tags=["ingestion"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["api_keys"])


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes-style deployments."""
    # Check database connectivity
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    # Check Redis connectivity
    try:
        import redis as redis_sync
        r = redis_sync.from_url(settings.redis_url)
        r.ping()
        redis_status = "connected"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_status = "disconnected"
    
    status_code = 200 if db_status == "connected" else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if db_status == "connected" else "not_ready",
            "database": db_status,
            "redis": redis_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()


@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation."""
    return {
        "message": "JobSwipe API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
