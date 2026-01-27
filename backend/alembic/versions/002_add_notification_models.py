"""Add notification models

Revision ID: 002_add_notification_models
Revises: 001_initial
Create Date: 2026-01-27 00:46:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_notification_models"
down_revision: Union[str, None] = "001_initial"  # noqa: F841 - Required by Alembic
branch_labels: Union[str, Sequence[str], None] = None  # noqa: F841 - Required by Alembic
depends_on: Union[str, Sequence[str], None] = None  # noqa: F841 - Required by Alembic


def upgrade() -> None:
    """Add notification preferences and device token tables."""

    # User notification preferences table
    op.create_table(
        "user_notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("push_enabled", sa.Boolean(), nullable=True),
        sa.Column("push_application_submitted", sa.Boolean(), nullable=True),
        sa.Column("push_application_completed", sa.Boolean(), nullable=True),
        sa.Column("push_application_failed", sa.Boolean(), nullable=True),
        sa.Column("push_captcha_detected", sa.Boolean(), nullable=True),
        sa.Column("push_job_match_found", sa.Boolean(), nullable=True),
        sa.Column("push_system_notification", sa.Boolean(), nullable=True),
        sa.Column("email_enabled", sa.Boolean(), nullable=True),
        sa.Column("email_application_submitted", sa.Boolean(), nullable=True),
        sa.Column("email_application_completed", sa.Boolean(), nullable=True),
        sa.Column("email_application_failed", sa.Boolean(), nullable=True),
        sa.Column("email_captcha_detected", sa.Boolean(), nullable=True),
        sa.Column("email_job_match_found", sa.Boolean(), nullable=True),
        sa.Column("email_system_notification", sa.Boolean(), nullable=True),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=True),
        sa.Column("quiet_hours_start", sa.String(), nullable=True),
        sa.Column("quiet_hours_end", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # Device tokens table
    op.create_table(
        "device_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("app_version", sa.String(), nullable=True),
        sa.Column("last_used", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.UniqueConstraint("user_id", "device_id", name="unique_user_device"),
    )

    # Notification templates table
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("title_template", sa.String(), nullable=False),
        sa.Column("message_template", sa.Text(), nullable=False),
        sa.Column("email_html_template", sa.Text(), nullable=True),
        sa.Column("channels", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    """Drop notification tables."""
    op.drop_table("notification_templates")
    op.drop_table("device_tokens")
    op.drop_table("user_notification_preferences")
