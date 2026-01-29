"""
MFA (Multi-Factor Authentication) Service
"""

import base64
import io
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pyotp
import qrcode

from backend.db.database import get_db
from backend.db.models import User


class MFAService:
    """Handles multi-factor authentication using TOTP (Time-based One-Time Password)"""

    def __init__(self):
        self.otp_expiry = timedelta(minutes=5)

    def generate_secret(self) -> str:
        """Generate a new secret key for TOTP"""
        return pyotp.random_base32()

    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """
        Generate a QR code for TOTP setup

        Args:
            user_email: User's email (for identification)
            secret: TOTP secret key

        Returns:
            Base64 encoded QR code image
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email, issuer_name="JobSwipe"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def verify_totp(self, secret: str, token: str) -> bool:
        """
        Verify a TOTP token

        Args:
            secret: TOTP secret key
            token: User-provided token

        Returns:
            True if token is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """
        Generate backup codes for MFA recovery

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def verify_backup_code(self, user: User, backup_code: str) -> bool:
        """
        Verify a backup code

        Args:
            user: User object
            backup_code: User-provided backup code

        Returns:
            True if backup code is valid, False otherwise
        """
        backup_code = backup_code.strip().upper()
        if hasattr(user, "mfa_backup_codes") and user.mfa_backup_codes:
            codes = user.mfa_backup_codes
            if backup_code in codes:
                codes.remove(backup_code)
                return True
        return False


mfa_service = MFAService()
