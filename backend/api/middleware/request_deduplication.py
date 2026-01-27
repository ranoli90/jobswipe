"""
Request Deduplication Middleware

Prevents duplicate requests from being processed multiple times.
Uses Redis to track recently seen request signatures.
"""

import hashlib
import hmac
import time
from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.config import settings


class RequestDeduplicationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to prevent duplicate request processing.

    Uses Redis to track recently seen request signatures based on:
    - HTTP method
    - Request path
    - Request body hash (for POST/PUT/PATCH)
    - User ID (if authenticated)

    This prevents issues like:
    - Double submissions of forms
    - Duplicate API calls from retries
    - Multiple webhook deliveries
    """

    # Cache TTL in seconds (default: 60 seconds)
    CACHE_TTL = 60

    # Endpoints to skip deduplication
    EXCLUDED_PATHS = [
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    def __init__(self, app: Callable, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self._redis: Optional[redis.Redis] = redis_client
        self._local_cache: dict[str, float] = {}

    async def get_redis(self) -> Optional[redis.Redis]:
        """Get or create Redis client"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception:
                pass
        return self._redis

    def _generate_request_signature(self, request: Request, body: bytes) -> str:
        """
        Generate a unique signature for the request.

        Combines:
        - HTTP method
        - Path
        - Body hash (if present)
        - User ID (if authenticated)
        """
        # Create signature components
        components = [
            request.method,
            request.url.path,
        ]

        # Add body hash for mutation methods
        if body and request.method in ("POST", "PUT", "PATCH"):
            body_hash = hashlib.sha256(body).hexdigest()
            components.append(body_hash)

        # Add user ID if available
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            components.append(str(user_id))

        # Create signature
        signature = ":".join(components)
        return f"req:{hashlib.sha256(signature.encode()).hexdigest()[:32]}"

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from deduplication"""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with deduplication"""
        # Skip excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Skip GET and DELETE requests (idempotent operations)
        if request.method in ("GET", "DELETE", "HEAD", "OPTIONS"):
            return await call_next(request)

        # Read request body
        body = await request.body()

        # Generate request signature
        signature = self._generate_request_signature(request, body)

        # Check Redis cache first
        redis_client = await self.get_redis()
        if redis_client:
            try:
                # Try to acquire lock with NX (only if not exists)
                lock_acquired = await redis_client.set(
                    signature,
                    str(time.time()),
                    nx=True,
                    ex=self.CACHE_TTL,
                )

                if not lock_acquired:
                    # Request was already processed recently
                    return JSONResponse(
                        status_code=409,
                        content={
                            "detail": "Duplicate request detected",
                            "message": "A similar request was processed recently. Please try again.",
                        },
                    )
            except Exception:
                # Redis error - proceed with request
                pass
        

        # Fallback to local cache
        current_time = time.time()
        if signature in self._local_cache:
            # Check if cache entry is still valid
            cached_time = self._local_cache.get(signature, 0)
            if current_time - cached_time < self.CACHE_TTL:
                return JSONResponse(
                    status_code=409,
                        content={
                            "detail": "Duplicate request detected",
                            "message": "A similar request was processed recently. Please try again.",
                        },
                    )

            # Update local cache
            self._local_cache[signature] = current_time

            # Clean up old entries
            self._local_cache = {
                k: v
                for k, v in self._local_cache.items()
                if current_time - v < self.CACHE_TTL
            }

        # Process request
        response = await call_next(request)

        return response


def create_deduplication_middleware() -> type:
    """
    Factory function to create deduplication middleware.

    Returns the middleware class that can be added to FastAPI app.
    """
    return RequestDeduplicationMiddleware
