"""Add compliance tables for GDPR and CCPA

Revision ID: 3a8f9c2d4e5b
Revises: 2db8062baa3d
Create Date: 2026-02-01 08:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a8f9c2d4e5b'
down_revision: Union[str, Sequence[str], None] = '2db8062baa3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add compliance tables for GDPR/CCPA."""

    # User Consent table - tracks user consent history
    op.create_table(
        'user_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consent_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('consent_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_consents_consent_type'), 'user_consents', ['consent_type'], unique=False)
    op.create_index(op.f('ix_user_consents_user_id'), 'user_consents', ['user_id'], unique=False)

    # Data Export Request table - tracks GDPR Article 20 requests
    op.create_table(
        'data_export_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('format', sa.String(), nullable=True),
        sa.Column('export_data', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_export_requests_status'), 'data_export_requests', ['status'], unique=False)
    op.create_index(op.f('ix_data_export_requests_user_id'), 'data_export_requests', ['user_id'], unique=False)

    # Data Deletion Request table - tracks GDPR Article 17 / CCPA deletion requests
    op.create_table(
        'data_deletion_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('grace_period_end', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_deletion_requests_status'), 'data_deletion_requests', ['status'], unique=False)
    op.create_index(op.f('ix_data_deletion_requests_user_id'), 'data_deletion_requests', ['user_id'], unique=False)

    # Compliance Audit Log table - tracks all compliance-related actions
    op.create_table(
        'compliance_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_audit_logs_action'), 'compliance_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_compliance_audit_logs_created_at'), 'compliance_audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_compliance_audit_logs_user_id'), 'compliance_audit_logs', ['user_id'], unique=False)

    # Cookie Consent table - tracks cookie preferences for GDPR
    op.create_table(
        'cookie_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('essential', sa.Boolean(), nullable=True),
        sa.Column('analytics', sa.Boolean(), nullable=True),
        sa.Column('marketing', sa.Boolean(), nullable=True),
        sa.Column('preferences', sa.Boolean(), nullable=True),
        sa.Column('do_not_track', sa.Boolean(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cookie_consents_session_id'), 'cookie_consents', ['session_id'], unique=False)
    op.create_index(op.f('ix_cookie_consents_user_id'), 'cookie_consents', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove compliance tables."""

    # Drop cookie_consents table
    op.drop_index(op.f('ix_cookie_consents_user_id'), table_name='cookie_consents')
    op.drop_index(op.f('ix_cookie_consents_session_id'), table_name='cookie_consents')
    op.drop_table('cookie_consents')

    # Drop compliance_audit_logs table
    op.drop_index(op.f('ix_compliance_audit_logs_user_id'), table_name='compliance_audit_logs')
    op.drop_index(op.f('ix_compliance_audit_logs_created_at'), table_name='compliance_audit_logs')
    op.drop_index(op.f('ix_compliance_audit_logs_action'), table_name='compliance_audit_logs')
    op.drop_table('compliance_audit_logs')

    # Drop data_deletion_requests table
    op.drop_index(op.f('ix_data_deletion_requests_user_id'), table_name='data_deletion_requests')
    op.drop_index(op.f('ix_data_deletion_requests_status'), table_name='data_deletion_requests')
    op.drop_table('data_deletion_requests')

    # Drop data_export_requests table
    op.drop_index(op.f('ix_data_export_requests_user_id'), table_name='data_export_requests')
    op.drop_index(op.f('ix_data_export_requests_status'), table_name='data_export_requests')
    op.drop_table('data_export_requests')

    # Drop user_consents table
    op.drop_index(op.f('ix_user_consents_user_id'), table_name='user_consents')
    op.drop_index(op.f('ix_user_consents_consent_type'), table_name='user_consents')
    op.drop_table('user_consents')
