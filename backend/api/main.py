#!/usr/bin/env python3
"""
JobSwipe API - Main Entry Point

FastAPI-based API for job search and application automation platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routers import auth, profile, jobs, applications, jobs_ingestion, analytics, application_automation, job_deduplication, job_categorization
from backend.metrics import MetricsMiddleware, metrics_endpoint
from backend.tracing import setup_tracing
from backend.db.database import get_db
from backend.services.embedding_service import EmbeddingService
import redis
import os
import uuid


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
                message["headers"] = message.get("headers", []) + [(b"x-correlation-id", correlation_id)]
            await send(message)

        await self.app(scope, receive, wrapped_send)


app = FastAPI(title="JobSwipe API", version="1.0.0")

# Setup OpenTelemetry tracing
setup_tracing(app)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Prometheus metrics middleware
app.add_middleware(MetricsMiddleware)

# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(profile.router, prefix="/v1/profile", tags=["profile"])
app.include_router(jobs.router, prefix="/v1/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/v1/applications", tags=["applications"])
app.include_router(jobs_ingestion.router, prefix="/v1/ingestion", tags=["ingestion"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])
app.include_router(application_automation.router, prefix="/v1/application-automation", tags=["application-automation"])
app.include_router(job_deduplication.router, tags=["deduplication"])
app.include_router(job_categorization.router, tags=["categorization"])


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "JobSwipe API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": "2026-01-25T00:00:00Z",
        "services": {}
    }

    # Check database connectivity
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
        db.close()
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis connectivity
    try:
        redis_url = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
        if redis_url.startswith("redis://"):
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "unknown"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check RabbitMQ connectivity (basic check)
    try:
        # For a simple check, we can try to connect to RabbitMQ management API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://rabbitmq:15672/api/overview", auth=("guest", "guest"), timeout=5.0)
            if response.status_code == 200:
                health_status["services"]["rabbitmq"] = "healthy"
            else:
                health_status["services"]["rabbitmq"] = f"unhealthy: HTTP {response.status_code}"
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["rabbitmq"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check embedding service
    try:
        if EmbeddingService.is_available():
            health_status["services"]["embedding_service"] = "healthy"
        else:
            health_status["services"]["embedding_service"] = "unhealthy"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["embedding_service"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()
