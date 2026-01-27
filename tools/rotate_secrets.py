#!/usr/bin/env python3
"""
Secret Rotation Script for JobSwipe

This script generates new cryptographically secure secrets and updates
environment configuration files. Use this to rotate secrets regularly
for security best practices.

Usage:
    python tools/rotate_secrets.py [--env-file .env.production] [--backup]

Options:
    --env-file: Path to the .env file to update (default: .env.production)
    --backup: Create backup of the original file before updating
"""

import argparse
import os
import secrets
import shutil
import string
from datetime import datetime
from pathlib import Path


def generate_secret(length=32):
    """Generate a cryptographically secure secret."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_hex_secret(length=32):
    """Generate a hex secret."""
    return secrets.token_hex(length)


def generate_urlsafe_secret(length=32):
    """Generate a URL-safe secret."""
    return secrets.token_urlsafe(length)


def update_env_file(env_file_path, secrets_dict, backup=False):
    """Update environment file with new secrets."""
    env_path = Path(env_file_path)

    if not env_path.exists():
        print(f"Warning: {env_file_path} does not exist. Creating new file.")
        env_path.touch()

    # Create backup if requested
    if backup:
        backup_path = env_path.with_suffix(
            f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        if env_path.exists():
            shutil.copy(env_path, backup_path)
            print(f"Backup created: {backup_path}")

    # Read existing content
    content = ""
    if env_path.exists():
        content = env_path.read_text()

    lines = content.split("\n")
    updated_lines = []
    updated_keys = set()

    # Update existing secrets
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            updated_lines.append(line)
            continue

        if "=" in line:
            key, _ = line.split("=", 1)
            key = key.strip()
            if key in secrets_dict:
                new_value = secrets_dict[key]
                updated_lines.append(f"{key}={new_value}")
                updated_keys.add(key)
                print(f"Updated: {key}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add new secrets that weren't in the file
    if updated_keys != set(secrets_dict.keys()):
        if updated_lines and not updated_lines[-1].strip() == "":
            updated_lines.append("")
        updated_lines.append("# Added by secret rotation script")
        for key, value in secrets_dict.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}")
                print(f"Added: {key}")

    # Write back
    env_path.write_text("\n".join(updated_lines) + "\n")
    print(f"Updated {env_file_path}")


def main():
    parser = argparse.ArgumentParser(description="Rotate secrets for JobSwipe")
    parser.add_argument(
        "--env-file",
        default=".env.production",
        help="Path to .env file to update (default: .env.production)",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before updating"
    )
    parser.add_argument(
        "--length",
        type=int,
        default=64,
        help="Length of generated secrets (default: 64)",
    )

    args = parser.parse_args()

    # Generate new secrets
    secret_length = args.length
    new_secrets = {
        "SECRET_KEY": generate_secret(secret_length),
        "ENCRYPTION_PASSWORD": generate_secret(secret_length),
        "ENCRYPTION_SALT": generate_hex_secret(32),
        "MINIO_ROOT_USER": generate_secret(20),
        "MINIO_ROOT_PASSWORD": generate_secret(40),
        "POSTGRES_PASSWORD": generate_secret(secret_length),
        "ANALYTICS_API_KEY": generate_urlsafe_secret(32),
        "INGESTION_API_KEY": generate_urlsafe_secret(32),
        "DEDUPLICATION_API_KEY": generate_urlsafe_secret(32),
        "CATEGORIZATION_API_KEY": generate_urlsafe_secret(32),
        "AUTOMATION_API_KEY": generate_urlsafe_secret(32),
        "OAUTH_STATE_SECRET": generate_secret(secret_length),
        "GRAFANA_ADMIN_PASSWORD": generate_secret(secret_length),
        "JWT_SECRET_KEY": generate_secret(secret_length),
    }

    print("Generated new secrets:")
    for key, value in new_secrets.items():
        print(f"  {key}={value[:20]}...")

    print(f"\nUpdating {args.env_file}...")
    update_env_file(args.env_file, new_secrets, args.backup)

    print("\nSecret rotation completed!")
    print("IMPORTANT: Restart your application services to use the new secrets.")
    print("Make sure to update any external services that use these secrets.")


if __name__ == "__main__":
    main()
