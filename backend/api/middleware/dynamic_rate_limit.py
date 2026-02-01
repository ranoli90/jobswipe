"""
Dynamic Rate Limiting Middleware

This middleware implements dynamic rate limiting based on user tier,
supporting anonymous, free, premium, and enterprise tiers with Redis-backed
sliding window rate limiting.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis_async
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Rate limit configurations per user tier
RATE_LIMITS = {
    "anonymous": {"requests": 60, "window": timedelta(minutes=1)},  # 60 requests per minute
    "free": {"requests": 100, "window": timedelta(minutes=1)},      # 100 requests per minute
    "premium": {"requests": 500, "window": timedelta(minutes=1)},   # 500 requests per minute
    "enterprise": {"requests": 2000, "window": timedelta(minutes=1)} # 2000 requests per minute
}

# Redis key prefix for rate limiting
RATE_LIMIT_PREFIX = "rate_limit"


class DynamicRateLimiter:
    """Handles dynamic rate limiting based on user tier"""

    def __init__(self):
        """Initialize the dynamic rate limiter with Redis"""
        try:
            self.redis = redis_async.from_url(settings.redis_url)
            logger.info("DynamicRateLimiter: Redis connection initialized")
        except Exception as e:
            logger.warning(f"DynamicRateLimiter: Failed to connect to Redis - rate limiting disabled: {e}")
            self.redis = None

    async def get_user_tier(self, request: Request) -> str:
        """
        Determine the user's tier from the request.

        This method extracts the user's tier from the request context.
        - Anonymous users (no authentication): "anonymous"
        - Authenticated users: Check user's subscription tier
        - API key users: Check API key's tier or rate limit
        """
        # Default to anonymous
        user_tier = "anonymous"

        # Check if user is authenticated (from auth middleware or dependencies)
        if hasattr(request.state, "user"):
            # If user is authenticated, check their tier (this would typically come from user profile)
            # For now, default to "free" for authenticated users
            # TODO: Replace with actual user tier from database
            user_tier = "free"

        # Check if API key is being used (from API key auth middleware)
        if hasattr(request.state, "api_key"):
            # For API key authentication, use the API key's rate limit or determine tier
            # For now, default to "premium" for API key users
            user_tier = "premium"

        logger.debug(f"DynamicRateLimiter: User tier determined as {user_tier}")
        return user_tier

    async def get_rate_limit_key(self, request: Request, user_tier: str) -> str:
        """Generate a unique rate limit key based on user tier and identifier"""
        # For authenticated users, use user ID
        if hasattr(request.state, "user_id"):
            return f"{RATE_LIMIT_PREFIX}:{user_tier}:user:{request.state.user_id}"

        # For API key users, use API key ID
        if hasattr(request.state, "api_key_id"):
            return f"{RATE_LIMIT_PREFIX}:{user_tier}:api_key:{request.state.api_key_id}"

        # For anonymous users, use IP address
        client_ip = get_remote_address(request)
        return f"{RATE_LIMIT_PREFIX}:{user_tier}:ip:{client_ip}"

    async def is_rate_limited(self, request: Request) -> Optional[dict]:
        """
        Check if the request is rate limited.

        Returns:
            None if not rate limited, or dict with retry_after and limit info if rate limited
        """
        # Skip rate limiting if Redis is not available
        if self.redis is None:
            logger.debug("DynamicRateLimiter: Redis not available, skipping rate limit check")
            return None

        user_tier = await self.get_user_tier(request)
        rate_limit_config = RATE_LIMITS.get(user_tier, RATE_LIMITS["anonymous"])
        rate_limit_key = await self.get_rate_limit_key(request, user_tier)

        now = datetime.utcnow()
        window_start = now - rate_limit_config["window"]

        # Get all timestamps in the current window
        timestamps = await self.redis.zrangebyscore(
            rate_limit_key,
            window_start.timestamp(),
            now.timestamp()
        )

        if len(timestamps) >= rate_limit_config["requests"]:
            # Calculate retry after time
            oldest_timestamp = float(timestamps[0])
            retry_after = (window_start.timestamp() - oldest_timestamp) + rate_limit_config["window"].total_seconds()

            logger.warning(
                "Rate limit exceeded",
                extra={
                    "user_tier": user_tier,
                    "key": rate_limit_key,
                    "current": len(timestamps),
                    "limit": rate_limit_config["requests"],
                    "retry_after": retry_after
                }
            )

            return {
                "retry_after": retry_after,
                "limit": rate_limit_config["requests"],
                "remaining": 0,
                "reset": (now + timedelta(seconds=retry_after)).timestamp(),
                "user_tier": user_tier
            }

        # Add current timestamp to the window
        await self.redis.zadd(rate_limit_key, {now.timestamp(): now.timestamp()})

        # Cleanup old entries outside the window (to prevent Redis from growing indefinitely)
        await self.redis.zremrangebyscore(
            rate_limit_key,
            0,
            window_start.timestamp()
        )

        # Set expiration for the key to clean up after window ends
        await self.redis.expire(rate_limit_key, int(rate_limit_config["window"].total_seconds()))

        remaining = rate_limit_config["requests"] - (len(timestamps) + 1)
        reset = (now + rate_limit_config["window"]).timestamp()

        logger.debug(
            "Rate limit check passed",
            extra={
                "user_tier": user_tier,
                "key": rate_limit_key,
                "current": len(timestamps) + 1,
                "remaining": remaining,
                "limit": rate_limit_config["requests"],
                "reset": reset
            }
        )

        return {
            "retry_after": 0,
            "limit": rate_limit_config["requests"],
            "remaining": remaining,
            "reset": reset,
            "user_tier": user_tier
        }


# Create singleton instance
dynamic_rate_limiter = DynamicRateLimiter()


async def add_rate_limit_headers(response: Response, rate_limit_info: dict):
    """Add rate limit headers to the response"""
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(int(rate_limit_info["reset"]))
    response.headers["X-RateLimit-Tier"] = rate_limit_info["user_tier"]

    if rate_limit_info["retry_after"] > 0:
        response.headers["Retry-After"] = str(int(rate_limit_info["retry_after"]))


class DynamicRateLimitMiddleware:
    """FastAPI middleware for dynamic rate limiting"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Check rate limit
        rate_limit_info = await dynamic_rate_limiter.is_rate_limited(request)

        if rate_limit_info is None:
            # Rate limiting disabled (Redis not available), proceed with request
            response = await call_next(request)
            return response

        if rate_limit_info["retry_after"] > 0:
            # Rate limit exceeded
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests for {rate_limit_info['user_tier']} tier",
                    "retry_after": int(rate_limit_info["retry_after"]),
                    "rate_limit": rate_limit_info["limit"],
                    "user_tier": rate_limit_info["user_tier"]
                }
            )
            add_rate_limit_headers(response, rate_limit_info)
            return response

        # Proceed with request
        response = await call_next(request)
        add_rate_limit_headers(response, rate_limit_info)
        return response


def add_dynamic_rate_limit_middleware(app):
    """Helper function to add dynamic rate limit middleware to the FastAPI app"""
    app.add_middleware(DynamicRateLimitMiddleware)
    logger.info("Dynamic rate limit middleware added to application")
