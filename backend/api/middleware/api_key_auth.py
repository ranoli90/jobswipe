"""
API Key Authentication Middleware

Validates API keys for internal service requests.
"""

import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.db.database import get_db
from backend.services.api_key_service import ApiKeyService


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Checks for the X-API-Key header and validates the key against the database.
    Only applies to routes starting with /api/v1/internal/
    """

    # Routes that require API key authentication
    INTERNAL_ROUTES_PREFIX = "/api/v1/internal/"

    # Routes that should skip API key auth (use JWT instead)
    SKIP_ROUTES = [
        "/api/v1/auth/",
        "/api/v1/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    def _should_authenticate(self, path: str) -> bool:
        """
        Determine if the request path should be authenticated with API key.

        Args:
            path: The request path

        Returns:
            True if API key auth should be applied
        """
        # Skip if path is in skip list
        for skip_route in self.SKIP_ROUTES:
            if path.startswith(skip_route):
                return False

        # Apply to internal routes
        return path.startswith(self.INTERNAL_ROUTES_PREFIX)

    def _extract_bearer_token(self, auth_header: Optional[str]) -> Optional[str]:
        """
        Extract the API key from the Authorization header.

        Supports:
        - X-API-Key header
        - Authorization: Bearer <key> header

        Args:
            auth_header: The Authorization header value

        Returns:
            The API key or None
        """
        return None

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process the request through API key authentication.
        """
        path = request.url.path

        # Skip authentication for non-internal routes
        if not self._should_authenticate(path):
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Missing API key",
                    "message": "X-API-Key header is required for this endpoint",
                },
            )

        # Validate the key
        try:
            # Get database session
            db_generator = get_db()
            db = next(db_generator)

            service = ApiKeyService(db)
            api_key_record = service.verify_key(api_key)

            if not api_key_record:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid API key",
                        "message": "The provided API key is invalid or has been revoked",
                    },
                )

            # Check rate limit
            is_allowed, current_count = service.check_rate_limit(api_key_record)

            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Rate limit of {api_key_record.rate_limit} requests/hour exceeded",
                        "current_count": current_count,
                        "limit": api_key_record.rate_limit,
                    },
                )

            # Store the API key record in request state for use in route handlers
            request.state.api_key = api_key_record

            # Continue processing
            response = await call_next(request)

            # Log usage after request completes
            try:
                start_time = request.state.get("_start_time", time.time())
                duration_ms = int((time.time() - start_time) * 1000)

                # Get client info
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent")

                # Determine error type from response
                error_type = None
                if response.status_code >= 400:
                    if response.status_code == 401:
                        error_type = "auth_error"
                    elif response.status_code == 403:
                        error_type = "forbidden"
                    elif response.status_code == 404:
                        error_type = "not_found"
                    elif response.status_code == 429:
                        error_type = "rate_limit"
                    elif response.status_code >= 500:
                        error_type = "server_error"
                    else:
                        error_type = "client_error"

                try:
                    service.log_usage(
                        api_key=api_key_record,
                        endpoint=path,
                        method=request.method,
                        status_code=response.status_code,
                        request_size=int(request.headers.get("content-length", 0)),
                        duration_ms=duration_ms,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        error_type=error_type,
                    )
                except Exception as e:
                # Don't fail the request if logging fails
                pass

            return response

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Authentication error",
                    "message": "An error occurred while validating the API key",
                },
            )


def require_api_key(*required_permissions: str):
    """
    Dependency function to require specific permissions on an API key.

    Usage:
        @router.get("/endpoint")
        async def endpoint(
            request: Request,
            api_key: ApiKey = Depends(require_api_key("ingestion", "jobs:write"))
        ):
            ...

    Args:
        *required_permissions: List of required permission strings

    Returns:
        Dependency function that validates permissions
    """

    async def check_permissions(request: Request):
        api_key = getattr(request.state, "api_key", None)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key authentication required",
            )

        if required_permissions:
            key_permissions = set(api_key.permissions)
            required = set(required_permissions)

            if not key_permissions.issuperset(required):
                missing = required - key_permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key missing required permissions: {', '.join(missing)}",
                )

        return api_key

    return check_permissions
