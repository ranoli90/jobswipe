"""
Secrets management utilities for JobSwipe
"""

import logging
import os
from typing import Any, Dict, Optional

import hvac

from backend.config import settings

# Vault secret paths as constants to avoid duplication
DATABASE_VAULT_PATH = "jobswipe/database"
OPENAI_VAULT_PATH = "jobswipe/openai"
JWT_VAULT_PATH = "jobswipe/jwt"
ENCRYPTION_VAULT_PATH = "jobswipe/encryption"


class SecretsManager:
    """Manages secrets using HashiCorp Vault"""

    def __init__(self):
        from backend.config import settings
        self.logger = logging.getLogger(__name__)
        self.vault_url = settings.vault_url
        self.vault_token = settings.vault_token
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to Vault"""
        try:
            self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
            if not self.client.is_authenticated():
                self.logger.warning(
                    "Vault authentication failed, falling back to environment variables"
                )
                self.client = None
        except Exception as e:
            self.logger.warning("Could not connect to Vault: %s, falling back to environment variables" % (e)
            )
            self.client = None

    def get_secret(
        self, path: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret from Vault

        Args:
            path: Vault secret path
            key: Secret key
            default: Default value if not found

        Returns:
            Secret value or default
        """
        if self.client:
            try:
                response = self.client.secrets.kv.v2.read_secret_version(path=path)
                if response and "data" in response and "data" in response["data"]:
                    value = response["data"]["data"].get(key)
                    if value is not None:
                        self.logger.info("AUDIT: Secret accessed from Vault - path: %s, key: %s", path, key)
                        return value
            except Exception as e:
                self.logger.warning("AUDIT: Failed to read secret from Vault - path: %s, key: %s, error: %s", path, key, str(e))

        # Fallback to environment variables
        env_key = f"{path.replace('/', '_').upper()}_{key.upper()}"
        value = os.getenv(env_key, default)
        if value is not None and value != default:
            self.logger.info("AUDIT: Secret accessed from environment - key: %s", env_key)
        elif value == default:
            self.logger.warning("AUDIT: Secret not found, using default - path: %s, key: %s", path, key)
        return value

    def set_secret(self, path: str, key: str, value: str):
        """
        Set a secret in Vault

        Args:
            path: Vault secret path
            key: Secret key
            value: Secret value
        """
        if self.client:
            try:
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path, secret={key: value}
                )
                self.logger.info("AUDIT: Secret set in Vault - path: %s, key: %s", path, key)
                return
            except Exception as e:
                self.logger.warning("AUDIT: Failed to set secret in Vault - path: %s, key: %s, error: %s", path, key, str(e))

        # Fallback: set environment variable (not persistent)
        env_key = f"{path.replace('/', '_').upper()}_{key.upper()}"
        os.environ[env_key] = value
        self.logger.warning("AUDIT: Secret stored in environment variable %s (not persistent)", env_key)

    def get_encryption_key(self) -> str:
        """Get encryption key for PII data"""
        return self.get_secret(
            ENCRYPTION_VAULT_PATH, "key", "dev-encryption-key-change-in-production"
        )

    def get_database_credentials(self) -> Dict[str, str]:
        """Get database credentials"""
        return {
            "host": self.get_secret(DATABASE_VAULT_PATH, "host", "postgres"),
            "port": self.get_secret(DATABASE_VAULT_PATH, "port", "5432"),
            "database": self.get_secret(DATABASE_VAULT_PATH, "database", "jobswipe"),
            "username": self.get_secret(DATABASE_VAULT_PATH, "username", "postgres"),
            "password": self.get_secret(DATABASE_VAULT_PATH, "password", "postgres"),
        }

    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return self.get_secret(OPENAI_VAULT_PATH, "api_key")

    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key"""
        return self.get_secret(JWT_VAULT_PATH, "secret_key", settings.secret_key)


# Global secrets manager instance
secrets_manager = SecretsManager()


def get_secret(path: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get secrets"""
    return secrets_manager.get_secret(path, key, default)


def get_encryption_key() -> str:
    """Get encryption key"""
    return secrets_manager.get_encryption_key()


def get_database_url() -> str:
    """Get database URL from secrets"""
    creds = secrets_manager.get_database_credentials()
    return f"postgresql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key"""
    return secrets_manager.get_openai_api_key()


def get_jwt_secret_key() -> str:
    """Get JWT secret key"""
    return secrets_manager.get_jwt_secret_key()
