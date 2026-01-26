"""
PII encryption utilities for JobSwipe
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional
from backend.vault_secrets import get_encryption_key


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

        # Generate a key from password (for development)
        password = os.getenv("ENCRYPTION_PASSWORD", "dev-encryption-password-change-in-production").encode()
        salt = os.getenv("ENCRYPTION_SALT", "dev-salt-change-in-production").encode()

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

        encrypted = self.fernet.encrypt(data.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_data: Encrypted string (base64 encoded)

        Returns:
            Decrypted string
        """
        if not encrypted_data:
            return encrypted_data

        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            # If decryption fails, return original data (for backward compatibility)
            print(f"Decryption failed: {e}")
            return encrypted_data


# Global encryptor instance
encryptor = PIIEncryptor()


def encrypt_pii(data: str) -> str:
    """Encrypt PII data"""
    return encryptor.encrypt(data)


def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt PII data"""
    return encryptor.decrypt(encrypted_data)