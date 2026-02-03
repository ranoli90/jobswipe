"""
Sentry Error Tracking Configuration for Fly.io Deployment

This module configures Sentry for error tracking and performance monitoring
in the JobSwipe backend application.

Usage:
    Set SENTRY_DSN environment variable to enable Sentry:
    export SENTRY_DSN="https://your-dsn@sentry.io/project-id"

    Set SENTRY_ENVIRONMENT to specify the deployment environment:
    export SENTRY_ENVIRONMENT="production"
"""

import logging
import os
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

logger = logging.getLogger(__name__)

# Sentry configuration
SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
SENTRY_PROFILES_SAMPLE_RATE: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))


def init_sentry() -> Optional[sentry_sdk.Hub]:
    """
    Initialize Sentry error tracking.

    Returns:
        Sentry hub if initialized successfully, None otherwise.
    """
    if not SENTRY_DSN:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return None

    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
            send_default_pii=False,  # Don't send personally identifiable information
            send_client_reports=True,
            debug=False,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
            ],
            # Configure which errors to ignore
            ignore_errors=[
                "SecurityError",
                "TimeoutError",
                "ConnectionError",
            ],
            # Configure before-send hook for additional filtering
            before_send=lambda event, hint: _before_send(event, hint),
        )

        logger.info(
            f"Sentry initialized - environment={SENTRY_ENVIRONMENT}, "
            f"traces_sample_rate={SENTRY_TRACES_SAMPLE_RATE}"
        )
        return sentry_sdk.Hub.current

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return None


def _before_send(event: dict, hint: dict) -> Optional[dict]:
    """
    Before-send hook for filtering events.

    Args:
        event: The event dict
        hint: Additional context about the event

    Returns:
        Modified event or None to drop the event
    """
    # Filter out certain errors
    if "exc_info" in hint:
        exc_type = hint["exc_info"][0]
        # Filter out expected/handled errors
        if exc_type in (KeyboardInterrupt, SystemExit):
            return None

    # Add additional context
    if "extra" not in event:
        event["extra"] = {}

    # Add deployment info
    event["extra"]["fly_io_deployment"] = True
    event["extra"]["environment"] = SENTRY_ENVIRONMENT

    return event


def capture_exception(exception: Exception, **kwargs) -> Optional[str]:
    """
    Capture an exception with Sentry.

    Args:
        exception: The exception to capture
        **kwargs: Additional context to attach

    Returns:
        Event ID if captured, None otherwise
    """
    if not SENTRY_DSN:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)

        return sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", **kwargs) -> Optional[str]:
    """
    Capture a message with Sentry.

    Args:
        message: The message to capture
        level: Log level (debug, info, warning, error, critical)
        **kwargs: Additional context to attach

    Returns:
        Event ID if captured, None otherwise
    """
    if not SENTRY_DSN:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)

        return sentry_sdk.capture_message(message, level)


def set_user_context(user_id: str, email: Optional[str] = None, **kwargs):
    """
    Set user context for error tracking.

    Args:
        user_id: The user ID
        email: Optional email address
        **kwargs: Additional user attributes
    """
    if not SENTRY_DSN:
        return

    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        **kwargs,
    })


def add_breadcrumb(category: str, message: str, data: dict = None, level: str = "info"):
    """
    Add a breadcrumb to the current trace.

    Args:
        category: Breadcrumb category
        message: Breadcrumb message
        data: Additional data
        level: Log level
    """
    if not SENTRY_DSN:
        return

    sentry_sdk.add_breadcrumb({
        "category": category,
        "message": message,
        "data": data or {},
        "level": level,
    })


def configure_for_fly_io():
    """
    Configure Sentry specifically for Fly.io deployment.

    Sets up Fly.io-specific context and monitoring.
    """
    if not SENTRY_DSN:
        logger.info("Sentry not configured - skipping Fly.io configuration")
        return

    # Get Fly.io specific metadata
    fly_app_name = os.getenv("FLY_APP_NAME", "unknown")
    fly_region = os.getenv("FLY_REGION", "unknown")
    fly_instance_id = os.getenv("FLY_INSTANCE_ID", "unknown")

    # Configure scope with Fly.io context
    sentry_sdk.set_tag("fly_app_name", fly_app_name)
    sentry_sdk.set_tag("fly_region", fly_region)
    sentry_sdk.set_tag("fly_instance_id", fly_instance_id)

    logger.info(
        f"Sentry configured for Fly.io - app={fly_app_name}, region={fly_region}"
    )


# Convenience function for Flask/FastAPI integration
def setup_fastapi_middleware(app):
    """
    Set up Sentry monitoring for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    if SENTRY_DSN:
        init_sentry()
        configure_for_fly_io()
        logger.info("Sentry middleware configured for FastAPI")
    else:
        logger.info("Sentry not configured - middleware not added")


if __name__ == "__main__":
    # Test Sentry configuration
    logging.basicConfig(level=logging.INFO)

    if SENTRY_DSN:
        init_sentry()
        configure_for_fly_io()

        # Test capture
        try:
            raise ValueError("Test exception for Sentry")
        except Exception as e:
            capture_exception(e, test=True)

        print("Sentry test completed - check your Sentry dashboard")
    else:
        print("SENTRY_DSN not set - skipping Sentry test")
        print("To enable Sentry, set the SENTRY_DSN environment variable")
