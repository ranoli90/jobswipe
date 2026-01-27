#!/usr/bin/env python3
"""
Migration Creation Helper Script

This script helps create new Alembic migrations with proper data migration support.
It provides templates and validation for schema changes that require data transformation.
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from alembic import command
from alembic.config import Config


class MigrationCreator:
    """Helper for creating database migrations with data migration support."""

    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.alembic_cfg = Config(str(self.backend_dir / "alembic.ini"))

    def create_migration(self, message: str, data_migration: bool = False) -> str:
        """Create a new migration with optional data migration template."""

        # Generate migration file
        command.revision(self.alembic_cfg, message=message, autogenerate=True)

        # Get the newly created migration file
        versions_dir = self.backend_dir / "alembic" / "versions"
        migration_files = sorted(versions_dir.glob("*.py"), reverse=True)

        if not migration_files:
            raise FileNotFoundError("No migration file was created")

        latest_migration = migration_files[0]

        if data_migration:
            self._add_data_migration_template(latest_migration)

        return str(latest_migration)

    def _add_data_migration_template(self, migration_file: Path):
        """Add data migration template to the migration file."""

        template = '''

    # Data migration section
    # Uncomment and modify the following blocks as needed for data transformations

    # Example: Migrate existing data
    # connection = op.get_bind()
    #
    # # Example 1: Update existing records
    # connection.execute(
    #     sa.text("""
    #         UPDATE users
    #         SET status = 'active'
    #         WHERE status IS NULL
    #     """)
    # )
    #
    # # Example 2: Migrate data between tables
    # connection.execute(
    #     sa.text("""
    #         INSERT INTO user_preferences (user_id, preference_key, preference_value)
    #         SELECT id, 'theme', 'light'
    #         FROM users
    #         WHERE id NOT IN (SELECT user_id FROM user_preferences WHERE preference_key = 'theme')
    #     """)
    # )
    #
    # # Example 3: Transform JSON data
    # connection.execute(
    #     sa.text("""
    #         UPDATE candidate_profiles
    #         SET skills = jsonb_set(skills, '{primary}', skills->'main_skill')
    #         WHERE skills ? 'main_skill'
    #     """)
    # )

    pass
'''

        # Read current content
        with open(migration_file, "r") as f:
            content = f.read()

        # Add data migration template before the final pass statement
        content = content.replace(
            "\n    pass\n\ndef downgrade", f"{template}\n    pass\n\ndef downgrade"
        )

        # Write back
        with open(migration_file, "w") as f:
            f.write(content)

    def validate_migration(self, migration_file: Path) -> List[str]:
        """Validate a migration file for common issues."""

        issues = []

        with open(migration_file, "r") as f:
            content = f.read()

        # Check for required functions
        if "def upgrade():" not in content:
            issues.append("Missing upgrade() function")

        if "def downgrade():" not in content:
            issues.append("Missing downgrade() function")

        # Check for potentially dangerous operations
        dangerous_patterns = [
            r"DROP TABLE.*CASCADE",
            r"DELETE FROM.*WHERE.*",
            r"UPDATE.*SET.*WHERE.*",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                issues.append(f"Potentially dangerous operation detected: {pattern}")

        # Check for transaction handling
        if "op.get_bind()" in content and "with op.get_bind():" not in content:
            issues.append("Raw database operations should be wrapped in transactions")

        return issues

    def create_data_migration(self, message: str, operations: List[Dict]) -> str:
        """Create a migration specifically for data operations."""

        # Generate basic migration
        migration_file = self.create_migration(f"data: {message}", data_migration=True)

        # Read and modify the migration
        migration_path = Path(migration_file)

        with open(migration_path, "r") as f:
            content = f.read()

        # Generate data migration code
        data_code = self._generate_data_migration_code(operations)

        # Replace the template
        content = content.replace(template, data_code)

        # Write back
        with open(migration_path, "w") as f:
            f.write(content)

        return migration_file

    def _generate_data_migration_code(self, operations: List[Dict]) -> str:
        """Generate data migration code from operations list."""

        code_lines = []

        for op in operations:
            op_type = op.get("type")

            if op_type == "update":
                table = op.get("table")
                set_clause = op.get("set")
                where_clause = op.get("where", "1=1")

                code_lines.append(f'''
    # Update operation: {op.get('description', 'Update records')}
    connection.execute(
        sa.text("""
            UPDATE {table}
            SET {set_clause}
            WHERE {where_clause}
        """)
    )''')

            elif op_type == "insert":
                table = op.get("table")
                columns = op.get("columns")
                values = op.get("values")

                code_lines.append(f'''
    # Insert operation: {op.get('description', 'Insert records')}
    connection.execute(
        sa.text("""
            INSERT INTO {table} ({columns})
            VALUES {values}
        """)
    )''')

            elif op_type == "delete":
                table = op.get("table")
                where_clause = op.get("where", "1=1")

                code_lines.append(f'''
    # Delete operation: {op.get('description', 'Delete records')}
    connection.execute(
        sa.text("""
            DELETE FROM {table}
            WHERE {where_clause}
        """)
    )''')

        return "\n".join(code_lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create database migrations with data migration support"
    )
    parser.add_argument("message", help="Migration message")
    parser.add_argument(
        "--data-migration", action="store_true", help="Include data migration template"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate existing migration"
    )

    args = parser.parse_args()

    creator = MigrationCreator()

    try:
        if args.validate:
            # Validate the latest migration
            versions_dir = Path(__file__).parent / "alembic" / "versions"
            migration_files = sorted(versions_dir.glob("*.py"), reverse=True)

            if not migration_files:
                logging.error("No migration files found to validate")
                sys.exit(1)

            latest_migration = migration_files[0]
            issues = creator.validate_migration(latest_migration)

            if issues:
                logging.error("Validation issues found in %s:", latest_migration.name)
                for issue in issues:
                    logging.error("  - %s", issue)
                sys.exit(1)

            logging.info("✅ Migration %s validated successfully", latest_migration.name)

        else:
            # Create new migration
            migration_file = creator.create_migration(args.message, args.data_migration)

            logging.info("✅ Created migration: %s", migration_file)

            if args.data_migration:
                logging.info("📝 Data migration template included")
                logging.info(
                    "   Edit the migration file to add your data transformation logic"
                )

    except Exception as e:
        logging.error("❌ Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
