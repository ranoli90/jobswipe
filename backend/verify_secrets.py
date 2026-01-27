#!/usr/bin/env python3
\"\"\"
Production Secrets Verification Script

This script verifies that all required secrets are properly set for production deployment.
Run this before deploying to production to ensure all security configurations are valid.
\"\"\"

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
    \"\"\"Check if a secret is properly set.\"\"\"
    value = os.getenv(name)
    
    if not value:
        return False, f\"{name} is not set\"
    
    # Check for forbidden placeholder values
    value_lower = value.lower()
    for forbidden in FORBIDDEN_VALUES:
        if value_lower.startswith(forbidden):
            return False, f\"{name} uses forbidden placeholder: {value}\"
    
    # Check for obviously weak values
    if len(value) < 16:
        return False, f\"{name} is too short ({len(value)} chars), minimum 16\"
    
    return True, f\"{name} is set\"


def check_optional_secrets() -> list[tuple[str, str, bool]]:
    \"\"\"Check optional secrets that have defaults.\"\"\"
    optional = {
        "REDIS_URL": "Redis connection URL (default: redis://localhost:6379/0)",
        "CELERY_BROKER_URL": "Celery broker URL (default: redis://localhost:6379/0)",
        "CELERY_RESULT_BACKEND": "Celery result backend (default: redis://localhost:6379/0)",
        "VAULT_URL": "Vault server URL (default: http://vault:8200)",
        "VAULT_TOKEN": "Vault authentication token",
        "OLLAMA_BASE_URL": "Ollama API URL (default: http://localhost:11434/v1)",
        "OLLAMA_MODEL": "Ollama model name (default: llama3.2:3b)",
        "OLLAMA_EMBEDDING_MODEL": "Ollama embedding model (default: nomic-embed-text)",
    }
    
    results = []
    for name, description in optional.items():
        value = os.getenv(name)
        if value:
            results.append((name, description, True))
        else:
            results.append((name, description, False))
    
    return results


def main():
    \"\"\"Main verification function.\"\"\"
    print(\"=\" * 60)
    print(\"Production Secrets Verification\")
    print(\"=\" * 60)
    print()
    
    # Check environment
    env = os.getenv(\"ENVIRONMENT\", \"unknown\")
    print(f\"Environment: {env}\")
    print()
    
    # Check required secrets
    print(\"Checking required secrets:\")
    print(\"-\" * 40)
    
    all_passed = True
    for name, description in REQUIRED_SECRETS.items():
        passed, message = check_secret(name, description)
        status = \"✅\" if passed else \"❌\"
        print(f\"{status} {name}: {message}\")
        if not passed:
            all_passed = False
    
    print()
    
    # Check optional secrets
    print(\"Checking optional secrets:\")
    print(\"-\" * 40)
    
    optional_results = check_optional_secrets()
    for name, description, is_set in optional_results:
        status = \"✅\" if is_set else \"⚠️\"
        print(f\"{status} {name}: {'set' if is_set else 'not set (using default)'}\")
    
    print()
    
    # Summary
    print(\"=\" * 60)
    if all_passed:
        print(\"✅ All required secrets are properly configured!\")
        return 0
    else:
        print(\"❌ Some required secrets are missing or invalid!\")
        print()
        print(\"To fix, set the missing secrets:\")
        print(\"  export SECRET_KEY='your-secure-secret-key'\")
        print(\"  # ... etc\")
        print()
        print(\"For Fly.io deployment:\")
        print(\"  flyctl secrets set SECRET_KEY='your-secure-secret-key' ...\")
        return 1


if __name__ == \"__main__\":
    sys.exit(main())
