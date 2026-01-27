"""
Domain Service - Handles domain rate limiting and configuration
"""

import json
import time
from typing import Any, Dict, Optional

from backend.db.database import get_db
from backend.db.models import Domain


class DomainRateLimiter:
    """Handles domain-specific rate limiting"""

    # Default rate limit constants
    DEFAULT_RPM = 10
    DEFAULT_RPH = 100
    DEFAULT_RPD = 500
    DEFAULT_CONCURRENCY = 5
    
    # Time window constants in seconds
    MINUTE = 60
    HOUR = 3600
    DAY = 86400

    def __init__(self):
        self.domain_limits: Dict[str, Dict[str, Any]] = {}
        self.request_timestamps: Dict[str, list] = {}
        self.load_domain_configs()

    def load_domain_configs(self):
        """Load domain configurations from database"""
        try:
            db = next(get_db())
            domains = db.query(Domain).all()

            for domain in domains:
                self.domain_limits[domain.host] = {
                    "rate_limit_policy": (
                        json.loads(domain.rate_limit_policy)
                        if domain.rate_limit_policy
                        else self._default_rate_limit()
                    ),
                    "ats_type": domain.ats_type,
                    "captcha_type": domain.captcha_type,
                    "last_status": domain.last_status,
                }

            db.close()
        except Exception as e:
            import logging

            logging.error(f"Error loading domain configurations: {str(e)}")
            # Use default config if database connection fails
            self.domain_limits = {}

    def _default_rate_limit(self):
        """Default rate limit policy"""
        return {
            "requests_per_minute": self.DEFAULT_RPM,
            "requests_per_hour": self.DEFAULT_RPH,
            "requests_per_day": self.DEFAULT_RPD,
            "concurrency": self.DEFAULT_CONCURRENCY,
        }

    def get_rate_limit(self, domain: str) -> Dict[str, Any]:
        """Get rate limit policy for a domain"""
        if domain not in self.domain_limits:
            self.domain_limits[domain] = {
                "rate_limit_policy": self._default_rate_limit(),
                "ats_type": "custom",
                "captcha_type": "none",
                "last_status": "active",
            }

        return self.domain_limits[domain]["rate_limit_policy"]

    def is_rate_limited(self, domain: str) -> bool:
        """Check if domain is rate limited"""
        rate_limit = self.get_rate_limit(domain)
        now = time.time()

        if domain not in self.request_timestamps:
            self.request_timestamps[domain] = []

        # Cleanup old timestamps
        self.request_timestamps[domain] = [
            ts
            for ts in self.request_timestamps[domain]
            if now - ts <= self.DAY  # Keep last 24 hours
        ]

        # Check rate limits
        minute_ago = now - self.MINUTE
        hour_ago = now - self.HOUR
        day_ago = now - self.DAY

        requests_last_minute = sum(
            1 for ts in self.request_timestamps[domain] if ts >= minute_ago
        )
        requests_last_hour = sum(
            1 for ts in self.request_timestamps[domain] if ts >= hour_ago
        )
        requests_last_day = sum(
            1 for ts in self.request_timestamps[domain] if ts >= day_ago
        )

        if (
            requests_last_minute >= rate_limit["requests_per_minute"]
            or requests_last_hour >= rate_limit["requests_per_hour"]
            or requests_last_day >= rate_limit["requests_per_day"]
        ):
            return True

        return False

    def record_request(self, domain: str):
        """Record a request to the domain"""
        if domain not in self.request_timestamps:
            self.request_timestamps[domain] = []

        self.request_timestamps[domain].append(time.time())

        # Cleanup old timestamps
        now = time.time()
        self.request_timestamps[domain] = [
            ts
            for ts in self.request_timestamps[domain]
            if now - ts <= self.DAY  # Keep last 24 hours
        ]

    def get_wait_time(self, domain: str) -> float:
        """Calculate time to wait before next request"""
        rate_limit = self.get_rate_limit(domain)
        now = time.time()

        if domain not in self.request_timestamps or not self.request_timestamps[domain]:
            return 0.0

        # Calculate time until rate limit resets
        minute_ago = now - self.MINUTE
        requests_last_minute = sum(
            1 for ts in self.request_timestamps[domain] if ts >= minute_ago
        )

        if requests_last_minute < rate_limit["requests_per_minute"]:
            return 0.0

        # Find the earliest request in the last minute to calculate wait time
        earliest_request = min(
            ts for ts in self.request_timestamps[domain] if ts >= minute_ago
        )
        time_until_reset = earliest_request + self.MINUTE - now

        return max(time_until_reset, 0.0)

    def update_domain_status(self, domain: str, status: str):
        """Update domain status"""
        if domain in self.domain_limits:
            self.domain_limits[domain]["last_status"] = status

        try:
            db = next(get_db())
            domain_record = db.query(Domain).filter(Domain.host == domain).first()
            if domain_record:
                domain_record.last_status = status
                db.commit()
            db.close()
        except Exception as e:
            import logging

            logging.error(f"Error updating domain status: {str(e)}")

    def set_rate_limit(self, domain: str, rate_limit_policy: Dict[str, Any]):
        """Set custom rate limit policy for domain"""
        if domain not in self.domain_limits:
            self.domain_limits[domain] = {
                "rate_limit_policy": rate_limit_policy,
                "ats_type": "custom",
                "captcha_type": "none",
                "last_status": "active",
            }
        else:
            self.domain_limits[domain]["rate_limit_policy"] = rate_limit_policy

        try:
            db = next(get_db())
            domain_record = db.query(Domain).filter(Domain.host == domain).first()
            if domain_record:
                domain_record.rate_limit_policy = json.dumps(rate_limit_policy)
                db.commit()
            else:
                new_domain = Domain(
                    host=domain,
                    rate_limit_policy=json.dumps(rate_limit_policy),
                    ats_type="custom",
                    captcha_type="none",
                    last_status="active",
                )
                db.add(new_domain)
                db.commit()
            db.close()
        except Exception as e:
            import logging

            logging.error(f"Error updating rate limit policy: {str(e)}")


class DomainService:
    """Service for managing domain configurations"""

    def __init__(self):
        self.rate_limiter = DomainRateLimiter()

    def get_domain_by_host(self, host: str):
        """Get domain configuration by host"""
        db = next(get_db())
        try:
            return db.query(Domain).filter(Domain.host == host).first()
        finally:
            db.close()

    def update_domain_status(self, host: str, status: str):
        """Update domain status"""
        self.rate_limiter.update_domain_status(host, status)

    def check_rate_limit(self, url: str) -> (bool, float):
        """Check if rate limit is exceeded for a given URL's domain

        Returns:
            Tuple of (rate_allowed: bool, retry_after: float) where retry_after
            is the number of seconds to wait before next request
        """
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        if self.rate_limiter.is_rate_limited(domain):
            retry_after = self.rate_limiter.get_wait_time(domain)
            return False, retry_after

        return True, 0.0

    def check_circuit_breaker(self, url: str) -> (bool, float):
        """Check if circuit breaker is tripped for a given URL's domain

        Returns:
            Tuple of (cb_allowed: bool, retry_after: float) where retry_after
            is the number of seconds to wait before next request
        """
        # For now, we'll just return True (circuit breaker not tripped) and 0 retry time
        return True, 0.0

    def get_rate_limiter(self) -> DomainRateLimiter:
        """Get the rate limiter instance"""
        return self.rate_limiter


# Create singleton instances
rate_limiter = DomainRateLimiter()
domain_service = DomainService()


def get_domain_rate_limiter() -> DomainRateLimiter:
    """Get the singleton rate limiter instance"""
    return rate_limiter


def get_domain_service() -> DomainService:
    """Get the singleton domain service instance"""
    return domain_service
