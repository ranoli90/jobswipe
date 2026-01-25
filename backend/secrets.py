"""
Secrets management utilities for JobSwipe
"""

import os
import hvac
from typing import Optional, Dict, Any


class SecretsManager:
    """Manages secrets using HashiCorp Vault"""

    def __init__(self):
        self.vault_url = os.getenv("VAULT_URL", "http://vault:8200")
        self.vault_token = os.getenv("VAULT_TOKEN", "dev-token-change-in-production")
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to Vault"""
        try:
            self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
            if not self.client.is_authenticated():
                print("Warning: Vault authentication failed, falling back to environment variables")
                self.client = None
        except Exception as e:
            print(f"Warning: Could not connect to Vault: {e}, falling back to environment variables")
            self.client = None

    def get_secret(self, path: str, key: str, default: Optional[str] = None) -> Optional[str]:
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
                if response and 'data' in response and 'data' in response['data']:
                    return response['data']['data'].get(key)
            except Exception as e:
                print(f"Error reading secret from Vault: {e}")

        # Fallback to environment variables
        env_key = f"{path.replace('/', '_').upper()}_{key.upper()}"
        return os.getenv(env_key, default)

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
                    path=path,
                    secret={key: value}
                )
                return
            except Exception as e:
                print(f"Error writing secret to Vault: {e}")

        # Fallback: set environment variable (not persistent)
        env_key = f"{path.replace('/', '_').upper()}_{key.upper()}"
        os.environ[env_key] = value
        print(f"Warning: Secret stored in environment variable {env_key} (not persistent)")

    def get_encryption_key(self) -> str:
        """Get encryption key for PII data"""
        return self.get_secret("jobswipe/encryption", "key", "dev-encryption-key-change-in-production")

    def get_database_credentials(self) -> Dict[str, str]:
        """Get database credentials"""
        return {
            "host": self.get_secret("jobswipe/database", "host", "postgres"),
            "port": self.get_secret("jobswipe/database", "port", "5432"),
            "database": self.get_secret("jobswipe/database", "database", "jobswipe"),
            "username": self.get_secret("jobswipe/database", "username", "postgres"),
            "password": self.get_secret("jobswipe/database", "password", "postgres")
        }

    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return self.get_secret("jobswipe/openai", "api_key")

    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key"""
        return self.get_secret("jobswipe/jwt", "secret_key", "dev-jwt-secret-change-in-production")


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