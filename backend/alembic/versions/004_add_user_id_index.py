"""Add user_id index to user_job_interactions for performance

Revision ID: 004_add_user_id_index
Revises: 003_add_default_notification_templates
Create Date: 2026-01-27

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_user_id_index"
down_revision: Union[str, None] = "003_add_default_notification_templates"  # noqa: F841 - Required by Alembic
branch_labels: Union[str, Sequence[str], None] = None  # noqa: F841 - Required by Alembic
depends_on: Union[str, Sequence[str], None] = None  # noqa: F841 - Required by Alembic


def upgrade() -> None:
    """Add index on user_id for user_job_interactions table."""
    # Create index for user_id column to improve query performance
    # when fetching user job history
    op.create_index(
        op.f("ix_user_job_interactions_user_id"),
        "user_job_interactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the user_id index."""
    op.drop_index(
        op.f("ix_user_job_interactions_user_id"), table_name="user_job_interactions"
    )
