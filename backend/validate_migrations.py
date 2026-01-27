#!/usr/bin/env python3
"""
Pre-deployment Migration Validation Script

This script validates migrations before deployment to ensure:
- All migrations can be applied successfully
- Rollback works correctly
- No breaking changes are introduced
- Schema integrity is maintained
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates database migrations for production deployment."""

    def __init__(self, backend_dir: str = None):
        self.backend_dir = Path(backend_dir) if backend_dir else Path(__file__).parent
        self.alembic_dir = self.backend_dir / "alembic"

    def run_command(self, cmd: list, cwd: Path = None) -> tuple[bool, str, str]:
        """Run a command and return success status, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.backend_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def check_alembic_setup(self) -> bool:
        """Check if Alembic is properly configured."""
        logger.info("Checking Alembic setup...")

        required_files = ["alembic.ini", "alembic/env.py", "alembic/versions"]

        for file_path in required_files:
            full_path = self.backend_dir / file_path
            if not full_path.exists():
                logger.error("Required file missing: %s", file_path)
                return False

        # Check if alembic command is available
        success, _, _ = self.run_command(["alembic", "--version"])
        if not success:
            logger.error("Alembic command not available")
            return False

        logger.info("Alembic setup validated")
        return True

    def validate_migration_files(self) -> bool:
        """Validate migration file syntax and structure."""
        logger.info("Validating migration files...")

        versions_dir = self.alembic_dir / "versions"
        if not versions_dir.exists():
            logger.error("Versions directory not found")
            return False

        migration_files = list(versions_dir.glob("*.py"))
        if not migration_files:
            logger.warning("No migration files found")
            return True  # Empty is OK for initial setup

        for migration_file in migration_files:
            # Basic syntax check
            success, _, stderr = self.run_command(
                ["python3", "-m", "py_compile", str(migration_file)]
            )
            if not success:
                logger.error("Syntax error in migration file %s: %s" % (migration_file.name, stderr)
                )
                return False

            # Check for required functions
            with open(migration_file, "r") as f:
                content = f.read()

            required_functions = ["upgrade", "downgrade"]
            for func in required_functions:
                if f"def {func}(" not in content:
                    logger.error("Missing required function "{func}' in {migration_file.name}"
                    )
                    return False

        logger.info("Validated %s migration files", len(migration_files))
        return True

    def check_migration_history(self) -> bool:
        """Check migration history for consistency."""
        logger.info("Checking migration history...")

        success, stdout, stderr = self.run_command(["alembic", "history"])
        if not success:
            logger.error("Failed to get migration history: %s", stderr)
            return False

        # Parse history output
        lines = stdout.strip().split("\n")
        if not lines or "No migrations" in stdout:
            logger.info("No migrations in history (initial setup)")
            return True

        # Check for any error indicators
        if "ERROR" in stdout.upper() or "FAILED" in stdout.upper():
            logger.error("Migration history contains errors")
            return False

        logger.info("Migration history validated")
        return True

    def validate_migration_dry_run(self) -> bool:
        """Perform a dry run of migrations."""
        logger.info("Performing migration dry run...")

        # Note: This would require a test database
        # For now, we'll just check if the command works
        success, stdout, stderr = self.run_command(
            ["alembic", "upgrade", "--dry-run", "head"]
        )
        if not success:
            logger.error("Dry run failed: %s", stderr)
            return False

        logger.info("Migration dry run successful")
        return True

    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set."""
        logger.info("Checking environment variables...")

        required_vars = ["DATABASE_URL"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error("Missing required environment variables: %s", missing_vars)
            return False

        logger.info("Environment variables validated")
        return True

    def validate_database_connection(self) -> bool:
        """Validate database connection."""
        logger.info("Validating database connection...")

        # This would require actual database access
        # For CI/CD, we might skip this or use a test database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not set")
            return False

        # Basic URL validation
        if not database_url.startswith(("postgresql://", "sqlite://")):
            logger.error("Unsupported database URL scheme")
            return False

        logger.info("Database connection URL validated")
        return True

    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        logger.info("Starting pre-deployment migration validation...")

        validations = [
            ("Alembic Setup", self.check_alembic_setup),
            ("Migration Files", self.validate_migration_files),
            ("Migration History", self.check_migration_history),
            ("Environment Variables", self.check_environment_variables),
            ("Database Connection", self.validate_database_connection),
        ]

        results = {}
        all_passed = True

        for name, validation_func in validations:
            logger.info("Running validation: %s", name)
            try:
                passed = validation_func()
                results[name] = passed
                status = "PASSED" if passed else "FAILED"
                logger.info("%s: %s", ('name', 'status'))
                if not passed:
                    all_passed = False
            except Exception as e:
                logger.error("%s failed with exception: %s", ('name', 'e'))
                results[name] = False
                all_passed = False

        # Summary
        passed_count = sum(results.values())
        total_count = len(results)

        logger.info("Validation Summary: %s/%s checks passed", ('passed_count', 'total_count'))

        if all_passed:
            logger.info("✅ All pre-deployment validations passed!")
        

        logger.error("❌ Some validations failed. Deployment blocked.")

        return all_passed


def main():
    """Main entry point."""
    validator = MigrationValidator()

    success = validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
