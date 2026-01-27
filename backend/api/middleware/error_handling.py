"""
Comprehensive Error Handling Middleware

Provides consistent error responses and logging across the API.
"""

import logging
import os
import sys
import traceback
from typing import Any, Callable, Dict, Optional, Type, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Add backend to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Raised when input validation fails"""

    def __init__(self, message: str, field_errors: list = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or []},
        )


class AuthenticationException(AppException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details={"requires_auth": True},
        )


class AuthorizationException(AppException):
    """Raised when user is not authorized to perform action"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message, status_code=403, error_code="AUTHORIZATION_ERROR"
        )


class NotFoundException(AppException):
    """Raised when a resource is not found"""

    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND")


class ConflictException(AppException):
    """Raised when there's a conflict (e.g., duplicate resource)"""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409, error_code="CONFLICT")


class RateLimitException(AppException):
    """Raised when rate limit is exceeded"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )


class ServiceUnavailableException(AppException):
    """Raised when an external service is unavailable"""

    def __init__(self, service: str):
        super().__init__(
            message=f"Service '{service}' is temporarily unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
        )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches all exceptions and returns consistent error responses.
    """

    # Maps exception types to HTTP status codes
    DEFAULT_STATUS_CODES: Dict[Type[Exception], int] = {
        HTTPException: 400,
        ValueError: 400,
        TypeError: 400,
        KeyError: 404,
        PermissionError: 403,
        FileNotFoundError: 404,
        NotImplementedError: 501,
    }

    # Error codes for common exceptions
    ERROR_CODES: Dict[Type[Exception], str] = {
        ValueError: "VALIDATION_ERROR",
        TypeError: "VALIDATION_ERROR",
        KeyError: "NOT_FOUND",
        AttributeError: "BAD_REQUEST",
        ZeroDivisionError: "BAD_REQUEST",
        OverflowError: "BAD_REQUEST",
        MemoryError: "INSUFFICIENT_RESOURCES",
    }

    def __init__(
        self,
        app,
        include_traceback: bool = False,
        log_level: str = "ERROR",
        safe_error_message: str = "An unexpected error occurred",
    ):
        super().__init__(app)
        self.include_traceback = include_traceback
        self.log_level = log_level
        self.safe_error_message = safe_error_message

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and handle any exceptions"""
        try:
            response = await call_next(request)
            return response

        except AppException as e:
            # Handle our custom app exceptions
            return self._handle_app_exception(request, e)

        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return self._handle_http_exception(request, e)

        except Exception as e:
            # Handle all other exceptions
            return self._handle_unexpected_exception(request, e)

    def _handle_app_exception(
        self, request: Request, exception: AppException
    ) -> JSONResponse:
        """Handle custom AppException"""
        # Log the error
        self._log_error(request, exception, exception.status_code)

        # Build error response
        error_response = {
            "success": False,
            "error": {
                "code": exception.error_code,
                "message": exception.message,
                "details": exception.details,
            },
            "request_id": getattr(request.state, "request_id", None),
        }

        return JSONResponse(
            status_code=exception.status_code,
            content=error_response,
            headers=exception.details.get("headers", {}),
        )

    def _handle_http_exception(
        self, request: Request, exception: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTPException"""
        # Log the error at warning level (these are expected)
        self._log_error(request, exception, exception.status_code, level="WARNING")

        error_response = {
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": (
                    str(exception.detail) if exception.detail else "Request failed"
                ),
                "details": {},
            },
            "request_id": getattr(request.state, "request_id", None),
        }

        return JSONResponse(
            status_code=exception.status_code,
            content=error_response,
            headers=exception.headers,
        )

    def _handle_unexpected_exception(
        self, request: Request, exception: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions"""
        # Determine status code
        status_code = self.DEFAULT_STATUS_CODES.get(type(exception), 500)

        error_code = self.ERROR_CODES.get(type(exception), "INTERNAL_ERROR")

        # Log the full error
        self._log_error(request, exception, status_code)

        # Build safe error response (don't expose internal details)
        error_response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": self.safe_error_message,
                "details": {"type": type(exception).__name__},
            },
            "request_id": getattr(request.state, "request_id", None),
        }

        # Include traceback in development
        if self.include_traceback:
            error_response["error"]["details"]["traceback"] = traceback.format_exc()

        return JSONResponse(status_code=status_code, content=error_response)

    def _log_error(
        self,
        request: Request,
        exception: Exception,
        status_code: int,
        level: str = None,
    ):
        """Log the error with context"""
        log_level = level or self.log_level

        # Build log context
        context = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": status_code,
            "exception_type": type(exception).__name__,
            "request_id": getattr(request.state, "request_id", None),
        }

        # Add user info if available
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            context["user_id"] = user_id

        # Add client IP
        if request.client:
            context["client_ip"] = request.client.host

        # Log at appropriate level
        log_message = str(exception)

        if log_level == "DEBUG":
            logger.debug(log_message, extra=context, exc_info=True)
        elif log_level == "INFO":
            logger.info(log_message, extra=context)
        elif log_level == "WARNING":
            logger.warning(log_message, extra=context)
        else:
            logger.error(log_message, extra=context, exc_info=True)

        # Log security-related errors to security logger
        if status_code in (401, 403):
            security_logger = logging.getLogger("security")
            security_logger.warning(
                f"Security event: {type(exception).__name__}",
                extra={
                    **context,
                    "event": type(exception).__name__,
                    "message": log_message,
                },
            )


def add_error_handling_middleware(
    app,
    include_traceback: bool = False,
    log_level: str = "ERROR",
    safe_error_message: str = "An unexpected error occurred",
):
    """
    Add error handling middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
        include_traceback: Include traceback in error responses (development only!)
        log_level: Logging level for errors
        safe_error_message: Generic error message for unexpected exceptions
    """
    app.add_middleware(
        ErrorHandlingMiddleware,
        include_traceback=include_traceback,
        log_level=log_level,
        safe_error_message=safe_error_message,
    )

    logger.info("Error handling middleware added")


# Utility function to create consistent error responses
def create_error_response(
    success: bool = False,
    code: str = "ERROR",
    message: str = "An error occurred",
    status_code: int = 400,
    details: Dict[str, Any] = None,
    request_id: str = None,
) -> Dict[str, Any]:
    """Create a consistent error response dictionary"""
    return {
        "success": success,
        "error": {"code": code, "message": message, "details": details or {}},
        "request_id": request_id,
    }
