"""
Common Pydantic validators for input sanitization and validation
"""

import html
import logging
import re
from typing import Any

from pydantic import validator

logger = logging.getLogger(__name__)


def sanitize_string(value: str) -> str:
    """Sanitize a string by removing dangerous content and encoding HTML"""
    if not isinstance(value, str):
        return value

    # Remove script tags and other dangerous elements
    value = re.sub(
        r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL
    )
    value = re.sub(
        r"<iframe[^>]*>.*?</iframe>", "", value, flags=re.IGNORECASE | re.DOTALL
    )
    value = re.sub(
        r"<object[^>]*>.*?</object>", "", value, flags=re.IGNORECASE | re.DOTALL
    )
    value = re.sub(
        r"<embed[^>]*>.*?</embed>", "", value, flags=re.IGNORECASE | re.DOTALL
    )

    # Encode HTML entities
    value = html.escape(value, quote=True)

    return value


def string_validator(field_name: str):
    """Create a validator for string fields that sanitizes input"""

    def validate_string(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError(f"{field_name} must be a string")
        sanitized = sanitize_string(v)
        if sanitized != v:
            logger.warning(f"Input sanitized for field {field_name}")
        return sanitized

    return validator(field_name, pre=True, allow_reuse=True)(validate_string)


def email_validator():
    """Validator for email fields with sanitization"""

    def validate_email(cls, v):
        if not v or len(v) > 255:
            raise ValueError("Email must be between 1 and 255 characters")
        # Sanitize first
        v = sanitize_string(v)
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v

    return validator("email", pre=True, allow_reuse=True)(validate_email)


def phone_validator():
    """Validator for phone numbers with sanitization"""

    def validate_phone(cls, v):
        if v is None:
            return v
        v = sanitize_string(v)
        # Basic phone validation - allow digits, spaces, hyphens, parentheses
        if not re.match(r"^[\d\s\-\(\)\+\.]+$", v):
            raise ValueError("Invalid phone number format")
        return v

    return validator("phone", pre=True, allow_reuse=True)(validate_phone)


def name_validator(field_name: str):
    """Validator for name fields"""

    def validate_name(cls, v):
        if v is None:
            return v
        v = sanitize_string(v)
        if len(v) > 100:
            raise ValueError(f"{field_name} must be less than 100 characters")
        return v

    return validator(field_name, pre=True, allow_reuse=True)(validate_name)
