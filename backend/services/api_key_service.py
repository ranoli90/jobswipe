"""
API Key Management Service

Provides secure API key generation, validation, and management for internal services.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db.models import ApiKey, ApiKeyUsageLog, User

logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ApiKeyService:
    """Service for managing API keys for internal service authentication"""

    # Key format: {prefix}_{full_key}
    KEY_PREFIX_LENGTH = 8
    FULL_KEY_LENGTH = 48  # Total key length after prefix

    def __init__(self, db: Session):
        self.db = db

    def generate_key(self) -> tuple[str, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (display_key, stored_key)
            - display_key: Full key to show to user (e.g., "jobswipe_sk_abc123...")
            - stored_key: Hashed version for storage
        """
        # Generate random bytes for the key
        random_bytes = secrets.token_bytes(self.FULL_KEY_LENGTH)
        # Generate a URL-safe base64 encoded key
        full_key = f"jobswipe_sk_{secrets.token_urlsafe(self.FULL_KEY_LENGTH)}"
        # Get prefix for identification (first KEY_PREFIX_LENGTH chars after prefix)
        prefix = full_key[: self.KEY_PREFIX_LENGTH]

        # Hash the key for storage
        key_hash = self._hash_key(full_key)

        return full_key, key_hash

    def _hash_key(self, key: str) -> str:
        """
        Hash an API key using bcrypt.

        Args:
            key: The plain API key

        Returns:
            bcrypt hash of the key
        """
        return pwd_context.hash(key)

    def verify_key(self, key: str) -> Optional[ApiKey]:
        """
        Verify an API key and return the associated ApiKey record.

        Args:
            key: The API key to verify

        Returns:
            ApiKey object if valid, None otherwise
        """
        prefix = key[: self.KEY_PREFIX_LENGTH]

        # Look up by prefix first (fast index lookup)
        api_key = (
            self.db.query(ApiKey)
            .filter(ApiKey.key_prefix == prefix, ApiKey.is_active == True)
            .first()
        )

        if not api_key:
            logger.warning(f"API key lookup failed for prefix: {prefix}")
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            logger.warning(f"API key expired: {prefix}")
            return None

        # Verify the key hash
        if not self._verify_key_hash(key, api_key.key_hash):
            logger.warning(f"API key hash mismatch: {prefix}")
            return None

        return api_key

    def _verify_key_hash(self, key: str, stored_hash: str) -> bool:
        """
        Verify a key against its hash.

        Args:
            key: The plain API key
            stored_hash: The stored bcrypt hash

        Returns:
            True if key matches, False otherwise
        """
        return pwd_context.verify(key, stored_hash)

    def create_api_key(
        self,
        name: str,
        service_type: str,
        created_by: User,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        rate_limit: int = 1000,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create a new API key.

        Args:
            name: Human-readable name for the key
            service_type: Type of service (ingestion, automation, analytics, webhook)
            created_by: User creating the key
            description: Optional description
            permissions: Optional list of permissions
            rate_limit: Requests per hour limit
            expires_at: Optional expiration datetime

        Returns:
            Dict containing the new API key details (including the plain key)
        """
        # Generate new key
        display_key, key_hash = self.generate_key()
        prefix = display_key[: self.KEY_PREFIX_LENGTH]

        api_key = ApiKey(
            key_prefix=prefix,
            key_hash=key_hash,
            name=name,
            description=description,
            service_type=service_type,
            permissions=permissions or [],
            rate_limit=rate_limit,
            expires_at=expires_at,
            created_by=created_by.id,
            is_active=True,
        )

        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        logger.info(f"Created API key: {prefix} for service: {service_type}")

        return {
            "id": str(api_key.id),
            "key": display_key,  # Only returned once at creation
            "key_prefix": prefix,
            "name": api_key.name,
            "service_type": api_key.service_type,
            "permissions": api_key.permissions,
            "rate_limit": api_key.rate_limit,
            "expires_at": (
                api_key.expires_at.isoformat() if api_key.expires_at else None
            ),
            "created_at": api_key.created_at.isoformat(),
        }

    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: UUID of the API key to revoke

        Returns:
            True if revoked, False if not found
        """
        api_key = self.db.query(ApiKey).filter(ApiKey.id == key_id).first()

        if not api_key:
            return False

        api_key.is_active = False
        self.db.commit()

        logger.info(f"Revoked API key: {api_key.key_prefix}")
        return True

    def rotate_api_key(self, key_id: str, created_by: User) -> Optional[Dict[str, Any]]:
        """
        Rotate an API key (revoke old and create new).

        Args:
            key_id: UUID of the API key to rotate
            created_by: User performing the rotation

        Returns:
            New key details dict if successful, None if original not found
        """
        api_key = self.db.query(ApiKey).filter(ApiKey.id == key_id).first()

        if not api_key:
            return None

        # Revoke old key
        api_key.is_active = False

        # Create new key with same settings
        new_key_details = self.create_api_key(
            name=f"{api_key.name} (rotated)",
            service_type=api_key.service_type,
            created_by=created_by,
            description=api_key.description,
            permissions=api_key.permissions,
            rate_limit=api_key.rate_limit,
            expires_at=api_key.expires_at,
        )

        self.db.commit()

        logger.info(f"Rotated API key: {api_key.key_prefix}")
        return new_key_details

    def get_api_keys(
        self, service_type: Optional[str] = None, active_only: bool = True
    ) -> List[ApiKey]:
        """
        List API keys.

        Args:
            service_type: Optional filter by service type
            active_only: Only return active keys

        Returns:
            List of ApiKey objects
        """
        query = self.db.query(ApiKey)

        if service_type:
            query = query.filter(ApiKey.service_type == service_type)

        if active_only:
            query = query.filter(ApiKey.is_active == True)

        return query.order_by(ApiKey.created_at.desc()).all()

    def get_api_key_by_id(self, key_id: str) -> Optional[ApiKey]:
        """
        Get an API key by ID.

        Args:
            key_id: UUID of the API key

        Returns:
            ApiKey object or None
        """
        return self.db.query(ApiKey).filter(ApiKey.id == key_id).first()

    def log_usage(
        self,
        api_key: ApiKey,
        endpoint: str,
        method: str,
        status_code: Optional[int] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        duration_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """
        Log API key usage.

        Args:
            api_key: The ApiKey being used
            endpoint: The endpoint accessed
            method: HTTP method
            status_code: Response status code
            request_size: Request body size in bytes
            response_size: Response body size in bytes
            duration_ms: Request duration in milliseconds
            ip_address: Client IP address
            user_agent: Client user agent
            error_type: Type of error if applicable
        """
        usage_log = ApiKeyUsageLog(
            api_key_id=api_key.id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            request_size=request_size,
            response_size=response_size,
            duration_ms=duration_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            error_type=error_type,
        )

        self.db.add(usage_log)

        # Update usage stats
        api_key.last_used_at = datetime.utcnow()
        api_key.last_used_ip = ip_address
        api_key.usage_count += 1

        self.db.commit()

    def check_rate_limit(self, api_key: ApiKey) -> tuple[bool, int]:
        """
        Check if the API key is within rate limit.

        Uses a sliding window approach to count requests in the last hour.

        Args:
            api_key: The ApiKey to check

        Returns:
            Tuple of (is_allowed, current_count)
        """
        from datetime import datetime, timedelta

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # Count requests in the last hour
        result = self.db.execute(
            text("""
                SELECT COUNT(*) FROM api_key_usage_logs
                WHERE api_key_id = :key_id
                AND created_at > :since
            """),
            {"key_id": api_key.id, "since": one_hour_ago},
        )

        count = result.scalar() or 0

        return count < api_key.rate_limit, count

    def get_usage_stats(
        self, key_id: str, since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an API key.

        Args:
            key_id: UUID of the API key
            since: Optional start time for stats

        Returns:
            Dict with usage statistics
        """
        since = since or datetime.utcnow() - timedelta(days=7)

        result = self.db.execute(
            text("""
                SELECT
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 END) as success_requests,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests,
                    AVG(duration_ms) as avg_duration_ms,
                    SUM(request_size) as total_request_bytes,
                    SUM(response_size) as total_response_bytes
                FROM api_key_usage_logs
                WHERE api_key_id = :key_id
                AND created_at > :since
            """),
            {"key_id": key_id, "since": since},
        )

        row = result.fetchone()

        return {
            "total_requests": row[0] or 0,
            "success_requests": row[1] or 0,
            "error_requests": row[2] or 0,
            "avg_duration_ms": round(row[3] or 0, 2),
            "total_request_bytes": row[4] or 0,
            "total_response_bytes": row[5] or 0,
        }
