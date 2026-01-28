"""
OpenTelemetry tracing configuration for JobSwipe API
"""

import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_tracing(app=None, celery_app=None):
    """Setup OpenTelemetry tracing with Jaeger exporter for production environments"""

    # Only enable tracing in production and staging environments
    environment = os.getenv("ENVIRONMENT", "development")
    if environment not in ["production", "staging"]:
        logger.info("Skipping OpenTelemetry tracing setup for development environment")
        return

    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=14268,
    )

    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrument FastAPI if app is provided
    if app:
        FastAPIInstrumentor().instrument_app(app)

    # Instrument HTTPX (for external API calls)
    HTTPXClientInstrumentor().instrument()

    # Instrument Celery if celery_app is provided
    if celery_app:
        CeleryInstrumentor().instrument(app=celery_app)
        logger.info("Celery instrumentation configured")

    logger.info("OpenTelemetry tracing configured with Jaeger exporter")


def get_tracer(name: str):
    """Get a tracer instance"""
    return trace.get_tracer(name)
