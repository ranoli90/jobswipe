"""Add cascade deletes, unique constraints, and indexes

Revision ID: 4b5c6d7e8f9a
Revises: 3a8f9c2d4e5b
Create Date: 2026-02-02 10:15:00.000000+00:00

This migration adds:
- Cascade delete constraints for data integrity
- Unique constraints to prevent duplicate data
- Performance indexes for frequently queried columns

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b5c6d7e8f9a'
down_revision: Union[str, Sequence[str], None] = '3a8f9c2d4e5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add cascade deletes, unique constraints, and indexes."""
    
    # ==================== CASCADE DELETE CONSTRAINTS ====================
    
    # 1. candidate_profiles.user_id -> ondelete="CASCADE"
    op.drop_constraint('candidate_profiles_user_id_fkey', 'candidate_profiles', type_='foreignkey')
    op.create_foreign_key(
        'candidate_profiles_user_id_fkey', 
        'candidate_profiles', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 2. user_notification_preferences.user_id -> ondelete="CASCADE"
    op.drop_constraint('user_notification_preferences_user_id_fkey', 'user_notification_preferences', type_='foreignkey')
    op.create_foreign_key(
        'user_notification_preferences_user_id_fkey',
        'user_notification_preferences', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 3. device_tokens.user_id -> ondelete="CASCADE"
    op.drop_constraint('device_tokens_user_id_fkey', 'device_tokens', type_='foreignkey')
    op.create_foreign_key(
        'device_tokens_user_id_fkey',
        'device_tokens', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 4. application_tasks.job_id -> ondelete="CASCADE"
    op.drop_constraint('application_tasks_job_id_fkey', 'application_tasks', type_='foreignkey')
    op.create_foreign_key(
        'application_tasks_job_id_fkey',
        'application_tasks', 'jobs',
        ['job_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 5. user_job_interactions.job_id -> ondelete="CASCADE"
    op.drop_constraint('user_job_interactions_job_id_fkey', 'user_job_interactions', type_='foreignkey')
    op.create_foreign_key(
        'user_job_interactions_job_id_fkey',
        'user_job_interactions', 'jobs',
        ['job_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 6. notifications.task_id -> ondelete="SET NULL"
    op.drop_constraint('notifications_task_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key(
        'notifications_task_id_fkey',
        'notifications', 'application_tasks',
        ['task_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # ==================== UNIQUE CONSTRAINTS ====================
    
    # 1. application_tasks: UniqueConstraint('user_id', 'job_id')
    op.create_unique_constraint(
        'uq_application_tasks_user_job',
        'application_tasks',
        ['user_id', 'job_id']
    )
    
    # 2. user_job_interactions: UniqueConstraint('user_id', 'job_id', 'action')
    op.create_unique_constraint(
        'uq_user_job_interactions_user_job_action',
        'user_job_interactions',
        ['user_id', 'job_id', 'action']
    )
    
    # 3. jobs: UniqueConstraint('source', 'external_id')
    op.create_unique_constraint(
        'uq_jobs_source_external_id',
        'jobs',
        ['source', 'external_id']
    )
    
    # 4. user_consents: UniqueConstraint('user_id', 'consent_type')
    op.create_unique_constraint(
        'uq_user_consents_user_consent_type',
        'user_consents',
        ['user_id', 'consent_type']
    )
    
    # ==================== ADDITIONAL INDEXES ====================
    
    # 1. jobs.external_id - for duplicate detection
    op.create_index(
        op.f('ix_jobs_external_id'),
        'jobs',
        ['external_id'],
        unique=False
    )
    
    # 2. application_tasks.user_id + status - for user applications query
    op.create_index(
        op.f('ix_application_tasks_user_id_status'),
        'application_tasks',
        ['user_id', 'status'],
        unique=False
    )
    
    # 3. notifications.user_id + read - for unread count
    op.create_index(
        op.f('ix_notifications_user_id_read'),
        'notifications',
        ['user_id', 'read'],
        unique=False
    )
    
    # 4. user_job_interactions.created_at - for analytics
    op.create_index(
        op.f('ix_user_job_interactions_created_at'),
        'user_job_interactions',
        ['created_at'],
        unique=False
    )
    
    # 5. api_key_usage_logs.api_key_id - for audit queries
    op.create_index(
        op.f('ix_api_key_usage_logs_api_key_id'),
        'api_key_usage_logs',
        ['api_key_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - remove cascade deletes, unique constraints, and indexes."""
    
    # ==================== DROP INDEXES ====================
    
    op.drop_index(op.f('ix_api_key_usage_logs_api_key_id'), table_name='api_key_usage_logs')
    op.drop_index(op.f('ix_user_job_interactions_created_at'), table_name='user_job_interactions')
    op.drop_index(op.f('ix_notifications_user_id_read'), table_name='notifications')
    op.drop_index(op.f('ix_application_tasks_user_id_status'), table_name='application_tasks')
    op.drop_index(op.f('ix_jobs_external_id'), table_name='jobs')
    
    # ==================== DROP UNIQUE CONSTRAINTS ====================
    
    op.drop_constraint('uq_user_consents_user_consent_type', 'user_consents', type_='unique')
    op.drop_constraint('uq_jobs_source_external_id', 'jobs', type_='unique')
    op.drop_constraint('uq_user_job_interactions_user_job_action', 'user_job_interactions', type_='unique')
    op.drop_constraint('uq_application_tasks_user_job', 'application_tasks', type_='unique')
    
    # ==================== RESTORE ORIGINAL FOREIGN KEYS (without cascade) ====================
    
    # Restore notifications.task_id (without cascade)
    op.drop_constraint('notifications_task_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key(
        'notifications_task_id_fkey',
        'notifications', 'application_tasks',
        ['task_id'], ['id']
    )
    
    # Restore user_job_interactions.job_id (without cascade)
    op.drop_constraint('user_job_interactions_job_id_fkey', 'user_job_interactions', type_='foreignkey')
    op.create_foreign_key(
        'user_job_interactions_job_id_fkey',
        'user_job_interactions', 'jobs',
        ['job_id'], ['id']
    )
    
    # Restore application_tasks.job_id (without cascade)
    op.drop_constraint('application_tasks_job_id_fkey', 'application_tasks', type_='foreignkey')
    op.create_foreign_key(
        'application_tasks_job_id_fkey',
        'application_tasks', 'jobs',
        ['job_id'], ['id']
    )
    
    # Restore device_tokens.user_id (without cascade)
    op.drop_constraint('device_tokens_user_id_fkey', 'device_tokens', type_='foreignkey')
    op.create_foreign_key(
        'device_tokens_user_id_fkey',
        'device_tokens', 'users',
        ['user_id'], ['id']
    )
    
    # Restore user_notification_preferences.user_id (without cascade)
    op.drop_constraint('user_notification_preferences_user_id_fkey', 'user_notification_preferences', type_='foreignkey')
    op.create_foreign_key(
        'user_notification_preferences_user_id_fkey',
        'user_notification_preferences', 'users',
        ['user_id'], ['id']
    )
    
    # Restore candidate_profiles.user_id (without cascade)
    op.drop_constraint('candidate_profiles_user_id_fkey', 'candidate_profiles', type_='foreignkey')
    op.create_foreign_key(
        'candidate_profiles_user_id_fkey',
        'candidate_profiles', 'users',
        ['user_id'], ['id']
    )
