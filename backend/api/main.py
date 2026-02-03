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
from datetime import datetime
from contextlib import closing
from contextvars import ContextVar
from urllib.parse import urlparse

import redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

# Try to import settings with proper error handling
try:
    from backend.config import Settings
    settings = Settings()
except Exception as e:
    environment = os.getenv("ENVIRONMENT", "development").lower()
    logging.getLogger(__name__).critical(
        f"Failed to load settings (ENVIRONMENT={environment}): {e}"
    )
    if environment == "production":
        sys.exit(1)
    else:
        logging.getLogger(__name__).warning(
            "Running in limited mode. Some features may not work."
        )
        settings = None

# Initialize Sentry error tracking (Fly.io deployment)
try:
    from backend.monitoring.sentry_config import init_sentry, configure_for_fly_io
    sentry_initialized = init_sentry() is not None
    if sentry_initialized:
        configure_for_fly_io()
        logging.getLogger(__name__).info("Sentry error tracking initialized successfully")
except Exception as e:
    logging.getLogger(__name__).warning(f"Sentry initialization failed: {e}")
    sentry_initialized = False

 # Import middleware modules with error handling
try:
    from backend.api.middleware.compression import add_compression_middleware
    from backend.api.middleware.error_handling import add_error_handling_middleware
    from backend.api.middleware.file_validation import \
        add_file_validation_middleware
    from backend.api.middleware.input_sanitization import \
        InputSanitizationMiddleware
    from backend.api.middleware.output_encoding import OutputEncodingMiddleware
    from backend.api.middleware.security_headers import SecurityHeadersMiddleware
    from backend.api.middleware.cookie_consent import CookieConsentMiddleware
    from backend.api.middleware.dynamic_rate_limit import add_dynamic_rate_limit_middleware
    from backend.metrics import MetricsMiddleware, metrics_endpoint
    from backend.tracing import setup_tracing
    middleware_available = True
except Exception as e:
    logging.getLogger(__name__).warning(f"Some middleware not available: {e}")
    middleware_available = False

# Import database and services with error handling
try:
    from backend.db.database import get_db, engine
    db_available = True
except Exception as e:
    print(f"Warning: Database not available: {e}", file=sys.stderr)
    db_available = False
    get_db = None
    engine = None

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "logs/app.log")
log_max_size = int(os.getenv("LOG_MAX_SIZE", 10485760))  # 10MB
log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))

# Detect availability of JSON logger
try:
    from pythonjsonlogger import jsonlogger  # noqa: F401
    have_json = True
except Exception:
    have_json = False

# Ensure log directories exist
try:
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)  # for security.log
except OSError as e:
    # Fallback to console-only logging
    log_file = None
    logging.getLogger(__name__).warning(f"Could not create log directory: {e}")

# Build logging config dynamically
formatters = {}
if have_json:
    formatters["default"] = {
        "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s %(service)s",
    }
    formatters["security"] = {
        "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "format": "%(asctime)s SECURITY %(levelname)s %(message)s %(ip)s %(user)s %(path)s %(request_id)s %(service)s",
    }
else:
    formatters["default"] = {
        "class": "logging.Formatter",
        "format": "%(asctime)s %(name)s %(levelname)s %(message)s [request_id=%(request_id)s] [service=%(service)s]",
    }
    formatters["security"] = {
        "class": "logging.Formatter",
        "format": "%(asctime)s SECURITY %(levelname)s %(message)s [ip=%(ip)s user=%(user)s path=%(path)s request_id=%(request_id)s service=%(service)s]",
    }

handlers = {
    "console": {
        "level": log_level,
        "class": "logging.StreamHandler",
        "formatter": "default",
        "stream": "ext://sys.stdout",
    }
}

if log_file:
    handlers["file"] = {
        "level": log_level,
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "filename": log_file,
        "maxBytes": log_max_size,
        "backupCount": log_backup_count,
    }
    handlers["security_file"] = {
        "level": "INFO",
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "security",
        "filename": "logs/security.log",
        "maxBytes": log_max_size,
        "backupCount": log_backup_count,
    }

root_handlers = ["console"] + (["file"] if "file" in handlers else [])
security_handlers = (["security_file"] if "security_file" in handlers else []) + ["console"]

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters,
    "handlers": handlers,
    "loggers": {
        "": {  # root logger
            "handlers": root_handlers,
            "level": log_level,
            "propagate": True,
        },
        "security": {
            "handlers": security_handlers,
            "level": "INFO",
            "propagate": False,
        },
    },
}


# Context-local request id for logging
request_id_var = ContextVar("request_id", default="unknown")


class StructuredLoggingFilter(logging.Filter):
    """Add structured fields to log records"""

    def filter(self, record):
        record.service = "jobswipe-api"
        record.request_id = request_id_var.get()
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
        corr_value = correlation_id.decode()

        # Store in scope for use in spans
        scope["correlation_id"] = corr_value

        # Set request_id in context var
        token = request_id_var.set(corr_value)

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = message.get("headers", []) + [
                    (b"x-correlation-id", correlation_id)
                ]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # Reset context var to previous state
            request_id_var.reset(token)


app = FastAPI(
    title="JobSwipe API", version="1.0.0", max_request_size=10 * 1024 * 1024
)  # 10MB limit


# Helper to determine environment consistently

def get_environment():
    try:
        return getattr(settings, 'environment', os.getenv('ENVIRONMENT', 'development')).lower()
    except Exception:
        return os.getenv('ENVIRONMENT', 'development').lower()

ENV = get_environment()

# Initialize rate limiter with Redis or fail fast in production
if settings:
    try:
        limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
        app.state.limiter = limiter
        logger.info("Redis rate limiter initialized successfully")
    except Exception as e:
        if ENV == "production":
            logger.critical(f"Redis rate limiter failed in production: {e}")
            sys.exit(1)
        else:
            limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
            app.state.limiter = limiter
            logger.warning(f"Redis rate limiter failed, using in-memory fallback: {e}")
else:
    if ENV == "production":
        logger.critical("Settings not loaded in production - cannot initialize rate limiter")
        sys.exit(1)
    else:
        limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
        app.state.limiter = limiter
        logger.warning("Settings not loaded, using in-memory rate limiter")


# Setup rate limiting with Redis fallback to in-memory
@app.on_event("startup")
async def startup():
    # Validate environment configuration on startup
    logger.info("Validating environment configuration...")
    if settings:
        try:
            # Settings are already validated during instantiation, but we log success
            logger.info("Environment configuration validation successful")
            logger.info("Environment: %s", settings.environment)
            logger.info("Debug mode: %s", settings.debug)
        except Exception as e:
            logger.error("Environment configuration validation failed: %s", e)
    else:
        logger.warning("Settings not available - running in limited mode")

    # Start metrics collection task
    try:
        from backend.monitoring.metrics_collector import start_metrics_collection
        start_metrics_collection(interval=60)  # Collect metrics every 60 seconds
        logger.info("Metrics collection task started successfully")
    except Exception as e:
        logger.warning(f"Failed to start metrics collection task: {str(e)}")


@app.on_event("shutdown")
async def shutdown():
    try:
        if engine is not None:
            engine.dispose()
            logger.info("Database engine disposed gracefully")
    except Exception as e:
        logger.warning(f"Database engine dispose failed: {e}")
    logger.info("Application shutdown complete")


# Rate limiters
auth_limiter = limiter.limit("5/minute")
api_limiter = limiter.limit("60/minute")
public_limiter = limiter.limit("100/minute")


# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    client_ip = request.client.host if request.client else "unknown"
    user_id = getattr(request.state, "user_id", "anonymous") if hasattr(request.state, "user_id") else "anonymous"

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

    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"},
        headers={"Retry-After": str(exc.retry_after)},
    )


# Setup OpenTelemetry tracing
if middleware_available:
    try:
        setup_tracing(app)
        logger.info("OpenTelemetry tracing initialized")
    except Exception as e:
        logger.warning("Failed to initialize tracing: %s", e)

def get_cors_origins():
    """
    Get validated CORS origins based on environment.

    In production:
    - Localhost origins are explicitly blocked
    - Only origins from CORS_ALLOW_ORIGINS env var are allowed
    - Wildcards are not permitted

    In development/staging:
    - Localhost origins are allowed for local development
    """
    if not settings:
        return []

    environment = getattr(settings, 'environment', 'development')
    origins = getattr(settings, 'cors_allow_origins', [])

    # Production: Strict validation
    if environment == 'production':
        blocked_hosts = {'localhost', '127.0.0.1', '::1', '0.0.0.0'}
        filtered_origins = []

        for origin in origins:
            try:
                host = urlparse(origin).hostname or ""
            except Exception:
                host = ""
            host_lower = host.lower()
            if host_lower in blocked_hosts:
                logger.warning(
                    f"SECURITY: Blocking localhost origin '{origin}' in production environment"
                )
                continue
            filtered_origins.append(origin)

        if not filtered_origins:
            logger.error(
                "SECURITY CRITICAL: No valid CORS origins configured for production. "
                "Please set CORS_ALLOW_ORIGINS environment variable with allowed origins."
            )
            return []

        return filtered_origins

    # Development/Staging: Allow configured origins including localhost
    return origins


def get_cors_credentials():
    """
    Get CORS credentials setting based on environment.

    Only allow credentials for trusted origins in production.
    """
    if not settings:
        return False

    environment = getattr(settings, 'environment', 'development')

    # In production, credentials are only allowed for explicitly configured origins
    if environment == 'production':
        # Check if we have valid non-localhost origins
        origins = get_cors_origins()
        if not origins:
            return False
        return getattr(settings, 'cors_allow_credentials', False)

    # Development/Staging: Use configured setting
    return getattr(settings, 'cors_allow_credentials', True)


# CORS configuration - using settings from config with security enhancements
if settings:
    cors_origins = get_cors_origins()
    cors_credentials = get_cors_credentials()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    logger.info(
        f"CORS configured for environment '{settings.environment}' with {len(cors_origins)} allowed origin(s)"
    )
    if cors_origins:
        logger.debug(f"Allowed CORS origins: {cors_origins}")
else:
    # In non-production, allow safe localhost defaults; fail fast only in production
    if ENV == 'production':
        raise RuntimeError(
            "Settings failed to load - cannot start with permissive CORS in production. "
            "Ensure all required environment variables are set."
        )
    default_origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"]
    )
    logger.warning("Settings not available - configured default localhost CORS for development")

# Add correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Add security middleware (only if available)
if middleware_available:
    try:
        app.add_middleware(SecurityHeadersMiddleware)
    except Exception as e:
        logger.warning(f"Failed to add SecurityHeadersMiddleware: {e}")
    try:
        app.add_middleware(InputSanitizationMiddleware)
    except Exception as e:
        logger.warning(f"Failed to add InputSanitizationMiddleware: {e}")
    try:
        app.add_middleware(OutputEncodingMiddleware)
    except Exception as e:
        logger.warning(f"Failed to add OutputEncodingMiddleware: {e}")
    try:
        app.add_middleware(CookieConsentMiddleware)
    except Exception as e:
        logger.warning(f"Failed to add CookieConsentMiddleware: {e}")

    # Add compression middleware
    try:
        add_compression_middleware(app)
    except Exception as e:
        logger.warning(f"Failed to add compression middleware: {e}")

    # Add file validation middleware
    try:
        add_file_validation_middleware(app)
    except Exception as e:
        logger.warning(f"Failed to add file validation middleware: {e}")

    # Add error handling middleware
    try:
        add_error_handling_middleware(app)
    except Exception as e:
        logger.warning(f"Failed to add error handling middleware: {e}")

    # Add dynamic rate limit middleware
    try:
        add_dynamic_rate_limit_middleware(app)
    except Exception as e:
        logger.warning(f"Failed to add dynamic rate limit middleware: {e}")

    # Add metrics middleware
    try:
        app.add_middleware(MetricsMiddleware)
    except Exception as e:
        logger.warning(f"Failed to add metrics middleware: {e}")
    try:
        app.add_middleware(SlowAPIMiddleware)
    except Exception as e:
        logger.warning(f"Failed to add SlowAPI middleware: {e}")

# Import routers after app is created to avoid circular dependency
from backend.api.routers import (analytics, application_automation,
                         applications, auth, job_categorization,
                         job_deduplication, jobs, jobs_ingestion,
                         notifications, profile, api_keys, compliance)
from backend.monitoring.dashboard import router as monitoring_router

# Include routers only if settings loaded successfully
if settings:
    try:
        app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
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
        app.include_router(compliance.router, prefix="/api/v1", tags=["compliance"])
        app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])
        logger.info("All API routers loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load some routers: {e}")


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
    db_status = "unknown"
    redis_status = "unknown"

    if db_available and get_db:
        try:
            with closing(next(get_db())) as db:
                db.execute(text("SELECT 1"))
                db_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "disconnected"
    else:
        db_status = "not_configured"

    # Check Redis connectivity with connection error handling
    if settings:
        try:
            r = redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
            r.ping()
            redis_status = "connected"
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}")
            redis_status = "disconnected"
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            redis_status = "disconnected"
        finally:
            try:
                r.close()
            except Exception:
                pass
    else:
        redis_status = "not_configured"

    # Determine readiness requirement based on environment/override
    require_db_ready_env = os.getenv("REQUIRE_DB_READY")
    if require_db_ready_env is None:
        require_db_ready = (ENV == 'production')
    else:
        require_db_ready = require_db_ready_env.lower() in ("1", "true", "yes")

    if require_db_ready:
        status_code = 200 if db_status == "connected" else 503
        overall = "ready" if db_status == "connected" else "not_ready"
    else:
        status_code = 200
        overall = "ready" if db_status == "connected" else "degraded"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "database": db_status,
            "redis": redis_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    if middleware_available:
        return metrics_endpoint()
    return {"status": "metrics not available"}


@app.get("/health/worker")
async def worker_health_check():
    """
    Health check endpoint for worker processes.

    Returns:
        Worker health status including active worker count
    """
    try:
        # Check if Celery is available
        from backend.workers.celery_app import celery_app
        # Try to ping the broker
        inspector = celery_app.control.inspect()
        # Get active workers
        active_workers = inspector.active()

        if active_workers:
            worker_count = len(active_workers)
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "worker_count": worker_count,
                "workers": list(active_workers.keys())
            }
        else:
            return {
                "status": "warning",
                "timestamp": datetime.utcnow().isoformat(),
                "worker_count": 0,
                "message": "No active workers found"
            }
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.get("/health/rabbitmq")
async def rabbitmq_health_check():
    """
    RabbitMQ health check endpoint.

    Checks RabbitMQ message broker connectivity and health status.

    Returns:
        RabbitMQ health status with latency and cluster information

    Response Codes:
        200: RabbitMQ is healthy
        503: RabbitMQ is unhealthy or unreachable
    """
    try:
        from backend.services.health_check_service import get_health_check_service
        from backend.config import settings

        # Build RabbitMQ management URL from broker URL
        rabbitmq_mgmt_url = None
        if settings and settings.celery_broker_url:
            # Convert amqp:// to http:// for management API
            broker_url = settings.celery_broker_url
            if "@" in broker_url:
                # Extract host from amqp://user:pass@host:port/vhost
                host_part = broker_url.split("@")[-1].split("/")[0]
                host = host_part.split(":")[0]
                rabbitmq_mgmt_url = f"http://{host}:15672/api/health"

        health_service = get_health_check_service(
            rabbitmq_url=rabbitmq_mgmt_url
        )
        result = await health_service.check_rabbitmq()

        status_code = 200 if result.status.value in ["healthy", "degraded"] else 503
        return JSONResponse(
            status_code=status_code,
            content=result.to_dict()
        )
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "rabbitmq",
                "status": "unhealthy",
                "message": "RabbitMQ health check failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@app.get("/health/opensearch")
async def opensearch_health_check():
    """
    OpenSearch health check endpoint.

    Checks OpenSearch cluster health and connectivity.

    Returns:
        OpenSearch health status with cluster information

    Response Codes:
        200: OpenSearch is healthy (green) or degraded (yellow)
        503: OpenSearch is unhealthy (red) or unreachable
    """
    try:
        from backend.services.health_check_service import get_health_check_service

        health_service = get_health_check_service()
        result = await health_service.check_opensearch()

        status_code = 200 if result.status.value in ["healthy", "degraded"] else 503
        return JSONResponse(
            status_code=status_code,
            content=result.to_dict()
        )
    except Exception as e:
        logger.error(f"OpenSearch health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "opensearch",
                "status": "unhealthy",
                "message": "OpenSearch health check failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@app.get("/health/celery")
async def celery_health_check():
    """
    Celery worker health check endpoint.

    Checks Celery worker availability and task processing status.

    Returns:
        Celery health status with worker count and statistics

    Response Codes:
        200: Celery workers are active
        503: No Celery workers available or unreachable
    """
    try:
        from backend.services.health_check_service import get_health_check_service

        health_service = get_health_check_service()
        result = await health_service.check_celery()

        status_code = 200 if result.status.value in ["healthy", "degraded"] else 503
        return JSONResponse(
            status_code=status_code,
            content=result.to_dict()
        )
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "celery",
                "status": "unhealthy",
                "message": "Celery health check failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Comprehensive health check endpoint for all services.

    Performs health checks on all dependencies:
    - Database (PostgreSQL)
    - Redis
    - RabbitMQ
    - OpenSearch
    - Celery workers

    Returns:
        Detailed health status for all services with overall system health

    Response Codes:
        200: All services are healthy
        200: Some services are degraded (with details)
        503: One or more services are unhealthy

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "total_latency_ms": 150.5,
            "services": {
                "database": {
                    "service": "database",
                    "status": "healthy",
                    "latency_ms": 25.3,
                    "message": "Database connection successful"
                },
                ...
            }
        }
    """
    try:
        from backend.services.health_check_service import get_health_check_service
        from backend.config import settings

        # Build RabbitMQ management URL
        rabbitmq_mgmt_url = None
        if settings and settings.celery_broker_url:
            broker_url = settings.celery_broker_url
            if "@" in broker_url:
                host_part = broker_url.split("@")[-1].split("/")[0]
                host = host_part.split(":")[0]
                rabbitmq_mgmt_url = f"http://{host}:15672/api/health"

        health_service = get_health_check_service(
            database_url=settings.database_url if settings else None,
            redis_url=settings.redis_url if settings else None,
            rabbitmq_url=rabbitmq_mgmt_url,
        )

        result = await health_service.check_all()

        # Determine HTTP status code based on overall status
        overall_status = result.get("status", "unknown")
        if overall_status == "healthy":
            status_code = 200
        elif overall_status == "degraded":
            status_code = 200  # Still return 200 but indicate degraded in body
        else:
            status_code = 503

        return JSONResponse(
            status_code=status_code,
            content=result
        )
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Health check failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation."""
    return {
        "message": "JobSwipe API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/csp-report")
async def csp_report(request: Request):
    """
    Content Security Policy violation reporting endpoint.

    Receives CSP violation reports from browsers when content is blocked
    by the Content-Security-Policy header. This helps identify:
    - Missing resources that should be allowed
    - Potential XSS attacks being blocked
    - Misconfigured CSP directives

    In production, these reports should be sent to a monitoring service
    like Sentry, DataDog, or a dedicated CSP reporting service.
    """
    try:
        body = await request.json()

        # Extract CSP report details
        csp_report = body.get("csp-report", {})

        # Log the violation for analysis
        violation_details = {
            "document_uri": csp_report.get("document-uri"),
            "referrer": csp_report.get("referrer"),
            "blocked_uri": csp_report.get("blocked-uri"),
            "violated_directive": csp_report.get("violated-directive"),
            "original_policy": csp_report.get("original-policy"),
            "source_file": csp_report.get("source-file"),
            "line_number": csp_report.get("line-number"),
            "column_number": csp_report.get("column-number"),
        }

        # Log to security logger for monitoring
        security_logger.warning(
            "CSP violation reported",
            extra={
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "violation": violation_details,
            },
        )

        # In production, you might want to:
        # 1. Send to external monitoring service (Sentry, etc.)
        # 2. Store in database for analysis
        # 3. Alert on suspicious patterns

        return {"status": "report received"}

    except Exception as e:
        # Log error but don't expose details to client
        security_logger.error(f"Failed to process CSP report: {e}")
        return {"status": "report received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
