"""Add email_verified field to User model

Revision ID: 006
Revises: 005
Create Date: 2026-01-27

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '006'
down_revision = '005'  # noqa: F841 - Required by Alembic
branch_labels = None  # noqa: F841 - Required by Alembic
depends_on = None  # noqa: F841 - Required by Alembic


def upgrade():
    # Add email_verified column to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False))
    
    # Set existing users to email_verified = True (backward compatibility)
    op.execute("UPDATE users SET email_verified = TRUE WHERE email_verified IS NULL OR email_verified = FALSE")


def downgrade():
    # Remove email_verified column
    op.drop_column('users', 'email_verified')
