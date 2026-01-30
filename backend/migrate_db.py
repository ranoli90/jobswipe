#!/usr/bin/env python3
"""
Database Migration Script
This script handles database migrations using Alembic.
It provides a simple interface to apply migrations to the database.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from alembic import command
from alembic.config import Config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migration operations."""

    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.alembic_cfg = Config(str(self.backend_dir / "alembic.ini"))

    def check_migrations(self) -> bool:
        """Check if migrations are needed without applying them."""
        logger.info("Checking if migrations are needed...")

        try:
            # Get current revision
            from sqlalchemy import create_engine
            from sqlalchemy.engine.base import Engine
            from sqlalchemy.exc import OperationalError

            # Get database URL from environment variable
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                return False

            # Check if we can connect to the database
            try:
                engine: Engine = create_engine(database_url)
                with engine.connect():
                    logger.info("Database connection successful")
            except OperationalError as e:
                logger.error(f"Database connection failed: {e}")
                return False

            # Check migration status
            from alembic.runtime.environment import EnvironmentContext
            from alembic.script import ScriptDirectory

            script = ScriptDirectory.from_config(self.alembic_cfg)
            head_rev = script.get_current_head()

            if not head_rev:
                logger.info("No migrations to apply (initial state)")
                return True

            with EnvironmentContext(self.alembic_cfg, script):
                # This is a simplified check - in reality, you'd need to
                # compare the current database revision with head
                logger.info(f"Head migration: {head_rev}")
                logger.info("Migrations may be needed")

            return True

        except Exception as e:
            logger.error(f"Error checking migrations: {e}")
            return False

    def apply_migrations(self) -> bool:
        """Apply all pending migrations to the database."""
        logger.info("Applying database migrations...")

        try:
            command.upgrade(self.alembic_cfg, "head")
            logger.info("✅ Migrations applied successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database migration script using Alembic"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if migrations are needed without applying them"
    )

    args = parser.parse_args()

    runner = MigrationRunner()

    if args.check:
        success = runner.check_migrations()
    else:
        success = runner.apply_migrations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
