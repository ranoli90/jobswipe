"""
PII encryption utilities for JobSwipe
"""

import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.config import settings
from backend.vault_secrets import get_encryption_key

logger = logging.getLogger(__name__)


class DecryptionError(Exception):
    """Custom exception for decryption failures"""

    pass


class PIIEncryptor:
    """Handles encryption/decryption of PII data"""

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryptor with a key.

        Args:
            key: Encryption key. If None, uses environment variable or generates one.
        """
        if key is None:
            key = self._get_or_create_key()

        self.fernet = Fernet(key)

    def _get_or_create_key(self) -> bytes:
        """Get encryption key from secrets manager or create one"""
        # Try to get key from secrets manager first
        try:
            key_string = get_encryption_key()
            if key_string and key_string != "dev-encryption-key-change-in-production":
                return base64.urlsafe_b64decode(key_string)
        except Exception:
            pass

        # Fallback to environment variables
        key_env = os.getenv("ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception:
                pass

        # Generate a key from password
        password = settings.encryption_password.encode()
        salt = settings.encryption_salt.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string.

        Args:
            data: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return data

        try:
            encrypted = self.fernet.encrypt(data.encode())
            result = encrypted.decode()
            logger.info(f"AUDIT: PII encryption successful - data length: {len(data)}")
            return result
        except Exception as e:
            logger.error(f"AUDIT: PII encryption failed - {str(e)}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_data: Encrypted string (base64 encoded)

        Returns:
            Decrypted string

        Raises:
            DecryptionError: If decryption fails
        """
        if not encrypted_data:
            return encrypted_data

        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            result = decrypted.decode()
            logger.info(
                f"AUDIT: PII decryption successful - data length: {len(result)}"
            )
            return result
        except InvalidToken as e:
            logger.warning(f"AUDIT: PII decryption failed - Invalid token - {str(e)}")
            raise DecryptionError("Failed to decrypt data: invalid token")
        except Exception as e:
            logger.warning(f"AUDIT: PII decryption failed - {str(e)}")
            raise DecryptionError(f"Failed to decrypt data: {str(e)}")


# Global encryptor instance
encryptor = PIIEncryptor()


def encrypt_pii(data: str) -> str:
    """Encrypt PII data"""
    return encryptor.encrypt(data)


def decrypt_pii(encrypted_data: str) -> str:
    """
    Decrypt PII data.

    Args:
        encrypted_data: Encrypted string (base64 encoded)

    Returns:
        Decrypted string

    Raises:
        DecryptionError: If decryption fails (e.g., invalid token, wrong key)
    """
    return encryptor.decrypt(encrypted_data)


# Re-export DecryptionError for external use
__all__ = ["DecryptionError", "encrypt_pii", "decrypt_pii"]
