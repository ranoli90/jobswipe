#!/usr/bin/env python3
"""
Production Secrets Verification Script

This script verifies that all required secrets are properly set for production deployment.
Run this before deploying to production to ensure all security configurations are valid.
"""

import os
import sys

# Required secrets for production
REQUIRED_SECRETS = {
    "SECRET_KEY": "JWT authentication secret key",
    "DATABASE_URL": "PostgreSQL connection URL",
    "ENCRYPTION_PASSWORD": "Password for deriving encryption key",
    "ENCRYPTION_SALT": "Salt for deriving encryption key",
    "OAUTH_STATE_SECRET": "OAuth2 state secret",
    "ANALYTICS_API_KEY": "Internal analytics service API key",
    "INGESTION_API_KEY": "Internal ingestion service API key",
    "DEDUPLICATION_API_KEY": "Internal deduplication service API key",
    "CATEGORIZATION_API_KEY": "Internal categorization service API key",
    "AUTOMATION_API_KEY": "Internal automation service API key",
}

# Forbidden placeholder values
FORBIDDEN_VALUES = [
    "dev-",
    "CHANGE_",
    "placeholder",
    "your-",
    "replace-",
    "xxx",
    "XXX",
    "example",
    "test",
]


def check_secret(name: str, description: str) -> tuple[bool, str]:
    """Check if a secret is properly set."""
    value = os.getenv(name)
    
    if not value:
        return False, f"{name} is not set"
    
    # Check for forbidden placeholder values
    for forbidden in FORBIDDEN_VALUES:
        if forbidden.lower() in value.lower():
            return False, f"{name} contains forbidden placeholder value: {forbidden}"
    
    # Check minimum length (secrets should be reasonably long)
    if len(value) < 16:
        return False, f"{name} is too short (minimum 16 characters)"
    
    return True, f"{name} is properly set"


def verify_secrets():
    """Verify all required secrets."""
    print("🔐 Production Secrets Verification")
    print("=" * 50)
    
    all_passed = True
    
    for name, description in REQUIRED_SECRETS.items():
        passed, message = check_secret(name, description)
        status = "✅" if passed else "❌"
        print(f"{status} {message}")
        
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("✅ All secrets are properly configured!")
        return 0
    else:
        print("❌ Some secrets are missing or improperly configured!")
        print("\nPlease set the missing secrets before deploying to production.")
        return 1


if __name__ == "__main__":
    sys.exit(verify_secrets())
