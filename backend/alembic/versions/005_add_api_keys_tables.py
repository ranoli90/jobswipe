"""Add API keys tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-27

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "005"
down_revision = "004"  # noqa: F841 - Required by Alembic
branch_labels = None  # noqa: F841 - Required by Alembic
depends_on = None  # noqa: F841 - Required by Alembic


def upgrade():
    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=sa.func.uuid_generate_v4(),
        ),
        sa.Column("key_prefix", sa.String(8), nullable=False, unique=True, index=True),
        sa.Column("key_hash", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("service_type", sa.String, nullable=False),
        sa.Column("permissions", postgresql.JSON, default=[]),
        sa.Column("rate_limit", sa.Integer, default=1000),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("last_used_at", sa.DateTime),
        sa.Column("last_used_ip", sa.String),
        sa.Column("usage_count", sa.Integer, default=0),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column(
            "updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()
        ),
        sa.UniqueConstraint("key_prefix", name="unique_key_prefix"),
    )

    # Create api_key_usage_logs table
    op.create_table(
        "api_key_usage_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=sa.func.uuid_generate_v4(),
        ),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.String, nullable=False),
        sa.Column("method", sa.String, nullable=False),
        sa.Column("status_code", sa.Integer),
        sa.Column("request_size", sa.Integer),
        sa.Column("response_size", sa.Integer),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("ip_address", sa.String),
        sa.Column("user_agent", sa.String),
        sa.Column("error_type", sa.String),
        sa.Column("created_at", sa.DateTime, default=sa.func.now(), index=True),
    )

    # Create indexes for better query performance
    op.create_index("idx_api_keys_service_type", "api_keys", ["service_type"])
    op.create_index("idx_api_keys_is_active", "api_keys", ["is_active"])
    op.create_index("idx_api_keys_created_at", "api_keys", ["created_at"])
    op.create_index(
        "idx_api_key_usage_logs_api_key_id", "api_key_usage_logs", ["api_key_id"]
    )


def downgrade():
    op.drop_index("idx_api_key_usage_logs_api_key_id", table_name="api_key_usage_logs")
    op.drop_index("idx_api_keys_created_at", table_name="api_keys")
    op.drop_index("idx_api_keys_is_active", table_name="api_keys")
    op.drop_index("idx_api_keys_service_type", table_name="api_keys")
    op.drop_table("api_key_usage_logs")
    op.drop_table("api_keys")
