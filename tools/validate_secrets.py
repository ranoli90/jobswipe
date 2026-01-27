#!/usr/bin/env python3
"""
Secret Validation Script for JobSwipe
Validates that all required secrets are properly configured before deployment.

Usage:
    python tools/validate_secrets.py [--env-file .env.production]

Options:
    --env-file: Path to the .env file to validate (default: .env.production)
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class SecretValidator:
    def __init__(self, env_file: str):
        self.env_file = Path(env_file)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """Validate all secrets in the environment file."""
        if not self.env_file.exists():
            self.errors.append(f"Environment file {self.env_file} does not exist")
            return False

        # Load environment variables from file
        env_vars = self._load_env_file()

        # Validate required secrets
        self._validate_required_secrets(env_vars)

        # Validate secret formats
        self._validate_secret_formats(env_vars)

        # Validate production-specific requirements
        self._validate_production_requirements(env_vars)

        return len(self.errors) == 0

    def _load_env_file(self) -> Dict[str, str]:
        """Load environment variables from file."""
        env_vars = {}
        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"\'"')
                        env_vars[key] = value
        except Exception as e:
            self.errors.append(f"Failed to read {self.env_file}: {e}")
        return env_vars

    def _validate_required_secrets(self, env_vars: Dict[str, str]) -> None:
        """Validate that all required secrets are present."""
        required_secrets = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "ENCRYPTION_PASSWORD",
            "ENCRYPTION_SALT",
            "ANALYTICS_API_KEY",
            "INGESTION_API_KEY",
            "DEDUPLICATION_API_KEY",
            "CATEGORIZATION_API_KEY",
            "AUTOMATION_API_KEY",
            "OAUTH_STATE_SECRET",
        ]

        for secret in required_secrets:
            if secret not in env_vars or not env_vars[secret]:
                self.errors.append(f"Missing required secret: {secret}")
            elif env_vars[secret].startswith(("dev-", "CHANGE_", "your_")):
                self.errors.append(
                    f"Invalid placeholder value for {secret}: {env_vars[secret][:20]}..."
                )

    def _validate_secret_formats(self, env_vars: Dict[str, str]) -> None:
        """Validate that secrets have appropriate formats and lengths."""
        # Database URL validation
        if "DATABASE_URL" in env_vars:
            db_url = env_vars["DATABASE_URL"]
            if not db_url.startswith("postgresql://"):
                self.errors.append(
                    "DATABASE_URL must be a PostgreSQL connection string"
                )
            elif "user:password@host:port/db" in db_url:
                self.errors.append("DATABASE_URL contains placeholder values")

        # Redis URL validation
        if "REDIS_URL" in env_vars:
            redis_url = env_vars["REDIS_URL"]
            if not redis_url.startswith("redis://"):
                self.errors.append("REDIS_URL must be a Redis connection string")

        # Secret length validation
        min_secret_lengths = {
            "SECRET_KEY": 32,
            "ENCRYPTION_PASSWORD": 32,
            "ENCRYPTION_SALT": 32,
            "OAUTH_STATE_SECRET": 32,
        }

        for secret, min_length in min_secret_lengths.items():
            if secret in env_vars and len(env_vars[secret]) < min_length:
                self.errors.append(
                    f"{secret} is too short (minimum {min_length} characters)"
                )

        # Hex validation for encryption salt
        if "ENCRYPTION_SALT" in env_vars:
            salt = env_vars["ENCRYPTION_SALT"]
            if not re.match(r"^[0-9a-fA-F]+$", salt):
                self.errors.append("ENCRYPTION_SALT must be a valid hex string")

        # API key validation (should be URL-safe)
        api_keys = [
            "ANALYTICS_API_KEY",
            "INGESTION_API_KEY",
            "DEDUPLICATION_API_KEY",
            "CATEGORIZATION_API_KEY",
            "AUTOMATION_API_KEY",
        ]
        for api_key in api_keys:
            if api_key in env_vars:
                key_value = env_vars[api_key]
                if not re.match(r"^[A-Za-z0-9_-]+$", key_value):
                    self.warnings.append(
                        f"{api_key} contains invalid characters (should be URL-safe)"
                    )

    def _validate_production_requirements(self, env_vars: Dict[str, str]) -> None:
        """Validate production-specific requirements."""
        if env_vars.get("ENVIRONMENT") == "production":
            # In production, ensure no development values
            dev_patterns = ["dev-", "localhost", "127.0.0.1", "test", "example"]
            sensitive_vars = ["DATABASE_URL", "REDIS_URL", "OLLAMA_BASE_URL"]

            for var in sensitive_vars:
                if var in env_vars:
                    value = env_vars[var].lower()
                    for pattern in dev_patterns:
                        if pattern in value:
                            self.warnings.append(
                                f"{var} contains development pattern '{pattern}' in production"
                            )

    def print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("❌ VALIDATION FAILED")
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("✅ VALIDATION PASSED")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate secrets for JobSwipe deployment"
    )
    parser.add_argument(
        "--env-file",
        default=".env.production",
        help="Path to .env file to validate (default: .env.production)",
    )

    args = parser.parse_args()

    validator = SecretValidator(args.env_file)
    success = validator.validate()
    validator.print_results()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
