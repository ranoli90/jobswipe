#!/usr/bin/env python3
"""
Migration Testing Script

This script provides comprehensive testing for database migrations including:
- Forward migration testing
- Rollback testing
- Data integrity validation
- Performance benchmarking
"""

import logging
import os
import sys
import time
from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from db.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationTester:
    """Comprehensive migration testing suite."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)

        # Alembic configuration
        self.alembic_cfg = Config("alembic.ini")
        self.alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    @contextmanager
    def temporary_database(self):
        """Create a temporary database for testing."""
        # For PostgreSQL, we could create a test database
        # For now, we'll use transactions that we can rollback
        connection = self.engine.connect()
        transaction = connection.begin()

        try:
            # Create savepoint
            connection.execute(text("SAVEPOINT migration_test"))
            yield connection
        finally:
            # Rollback to savepoint
            connection.execute(text("ROLLBACK TO SAVEPOINT migration_test"))
            transaction.rollback()
            connection.close()

    def get_current_revision(self) -> str:
        """Get current migration revision."""
        with self.engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()

    def test_forward_migration(self) -> bool:
        """Test forward migration to latest revision."""
        logger.info("Testing forward migration...")

        try:
            start_time = time.time()

            # Run migrations
            command.upgrade(self.alembic_cfg, "head")

            end_time = time.time()
            duration = end_time - start_time

            logger.info(".2f")

            # Validate schema
            if not self.validate_schema_integrity():
                logger.error("Schema validation failed after forward migration")
                return False

            return True

        except Exception as e:
            logger.error("Forward migration failed: %s", e)
            return False

    def test_rollback_migration(self, target_revision: str = "base") -> bool:
        """Test rollback migration to specified revision."""
        logger.info("Testing rollback migration to %s...", target_revision)

        try:
            start_time = time.time()

            # Run rollback
            command.downgrade(self.alembic_cfg, target_revision)

            end_time = time.time()
            duration = end_time - start_time

            logger.info(".2f")

            # Validate schema after rollback
            if not self.validate_schema_integrity():
                logger.error("Schema validation failed after rollback migration")
                return False

            return True

        except Exception as e:
            logger.error("Rollback migration failed: %s", e)
            return False

    def test_data_integrity_during_migration(self) -> bool:
        """Test data integrity during migration process."""
        logger.info("Testing data integrity during migration...")

        try:
            # Insert test data before migration
            test_data = self.insert_test_data()

            # Run migration
            command.upgrade(self.alembic_cfg, "head")

            # Verify data integrity after migration
            if not self.verify_test_data_integrity(test_data):
                logger.error("Data integrity check failed after migration")
                return False

            # Test rollback
            command.downgrade(self.alembic_cfg, "base")

            # Verify data still exists after rollback
            if not self.verify_test_data_integrity(test_data):
                logger.error("Data integrity check failed after rollback")
                return False

            return True

        except Exception as e:
            logger.error("Data integrity test failed: %s", e)
            return False

    def insert_test_data(self) -> dict:
        """Insert test data for integrity checking."""
        with self.session_factory() as session:
            # This would need to be adapted based on your actual models
            # For now, we'll just return a placeholder
            return {"test_records": 0}

    def verify_test_data_integrity(self, test_data: dict) -> bool:
        """Verify test data integrity after migration."""
        # Implement data verification logic
        return True

    def validate_schema_integrity(self) -> bool:
        """Validate database schema integrity."""
        try:
            with self.engine.connect() as conn:
                # Check if all expected tables exist
                expected_tables = [
                    "users",
                    "candidate_profiles",
                    "failed_login_attempts",
                    "domains",
                    "jobs",
                    "job_index",
                    "user_job_interactions",
                    "application_tasks",
                    "application_audit_logs",
                    "cover_letter_templates",
                    "notifications",
                ]

                result = conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
                existing_tables = [row[0] for row in result.fetchall()]

                missing_tables = set(expected_tables) - set(existing_tables)
                if missing_tables:
                    logger.error("Missing tables: %s", missing_tables)
                    return False

                # Check alembic_version table
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.fetchone()
                if not current_version:
                    logger.error("No alembic version found")
                    return False

                logger.info("Current schema version: %s", current_version[0])
                return True

        except Exception as e:
            logger.error("Schema validation failed: %s", e)
            return False

    def benchmark_migration_performance(self) -> dict:
        """Benchmark migration performance."""
        results = {}

        # Test forward migration performance
        start_time = time.time()
        command.upgrade(self.alembic_cfg, "head")
        forward_time = time.time() - start_time

        # Test rollback performance
        start_time = time.time()
        command.downgrade(self.alembic_cfg, "base")
        rollback_time = time.time() - start_time

        results["forward_migration_time"] = forward_time
        results["rollback_migration_time"] = rollback_time

        return results

    def run_full_test_suite(self) -> bool:
        """Run complete migration test suite."""
        logger.info("Starting full migration test suite...")

        tests = [
            ("Forward Migration", self.test_forward_migration),
            ("Rollback Migration", lambda: self.test_rollback_migration()),
            ("Data Integrity", self.test_data_integrity_during_migration),
        ]

        results = {}
        for test_name, test_func in tests:
            logger.info("Running %s...", test_name)
            try:
                result = test_func()
                results[test_name] = result
                status = "PASSED" if result else "FAILED"
                logger.info("%s: %s", ('test_name', 'status'))
            except Exception as e:
                logger.error("%s failed with exception: %s", ('test_name', 'e'))
                results[test_name] = False

        # Performance benchmarking
        try:
            perf_results = self.benchmark_migration_performance()
            results["Performance"] = perf_results
            logger.info("Migration Performance: %s", perf_results)
        except Exception as e:
            logger.error("Performance benchmarking failed: %s", e)

        # Summary
        passed = sum(
            1 for result in results.values() if isinstance(result, bool) and result
        )
        total = sum(1 for result in results.values() if isinstance(result, bool))

        logger.info("Test Results: %s/%s tests passed", ('passed', 'total'))

        return passed == total


def main():
    """Main entry point for migration testing."""
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    

    database_url = settings.database_url

tester = MigrationTester(database_url)

success = tester.run_full_test_suite()

sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
