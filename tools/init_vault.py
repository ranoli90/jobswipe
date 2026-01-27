#!/usr/bin/env python3
"""
Initialize HashiCorp Vault with default secrets for JobSwipe
"""

import os
import sys
import time

import hvac


def init_vault():
    """Initialize Vault with default secrets"""

    vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
    vault_token = os.getenv("VAULT_TOKEN", "dev-token-change-in-production")

    print(f"Connecting to Vault at {vault_url}")

    # Wait for Vault to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            client = hvac.Client(url=vault_url, token=vault_token)
            if client.is_authenticated():
                print("Vault connection successful")
                break
            else:
                print(
                    f"Vault authentication failed (attempt {attempt + 1}/{max_attempts})"
                )
        except Exception as e:
            print(
                f"Vault connection failed (attempt {attempt + 1}/{max_attempts}): {e}"
            )

        if attempt < max_attempts - 1:
            time.sleep(2)
    else:
        print("Failed to connect to Vault after all attempts")
        return False

    # Enable KV v2 secrets engine if not already enabled
    try:
        client.sys.enable_secrets_engine(
            backend_type="kv", path="jobswipe", options={"version": 2}
        )
        print("Enabled KV v2 secrets engine at path 'jobswipe'")
    except Exception as e:
        if "path is already in use" in str(e):
            print("KV v2 secrets engine already enabled")
        else:
            print(f"Failed to enable KV secrets engine: {e}")
            return False

    # Set default secrets
    secrets = {
        "jobswipe/encryption": {
            "key": "dev-encryption-key-change-in-production"  # In production, use a proper base64-encoded key
        },
        "jobswipe/database": {
            "host": "postgres",
            "port": "5432",
            "database": "jobswipe",
            "username": "postgres",
            "password": "postgres",
        },
        "jobswipe/jwt": {"secret_key": "dev-jwt-secret-change-in-production"},
        "jobswipe/openai": {"api_key": ""},  # Leave empty for development
        "jobswipe/oauth2/google": {
            "client_id": "",  # Configure in production
            "client_secret": "",
        },
        "jobswipe/oauth2/linkedin": {
            "client_id": "",  # Configure in production
            "client_secret": "",
        },
    }

    for path, secret_data in secrets.items():
        try:
            client.secrets.kv.v2.create_or_update_secret(path=path, secret=secret_data)
            print(f"Set secrets at path: {path}")
        except Exception as e:
            print(f"Failed to set secrets at path {path}: {e}")
            return False

    print("Vault initialization completed successfully")
    return True


if __name__ == "__main__":
    success = init_vault()
    sys.exit(0 if success else 1)
