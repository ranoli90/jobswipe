"""
Database Models

Defines SQLAlchemy ORM models for the application.
"""

import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from backend.db.database import Base
from backend.encryption import decrypt_pii, encrypt_pii


class EncryptedString(TypeDecorator):
    """SQLAlchemy type decorator for encrypting PII strings"""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database"""
        if value is not None:
            return encrypt_pii(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt value when retrieving from database"""
        if value is not None:
            return decrypt_pii(value)
        return value


class User(Base):
    """User model"""

    __tablename__ = "users"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # MFA fields
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String)
    mfa_backup_codes = Column(JSON)

    # Security fields
    lockout_until = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("CandidateProfile", uselist=False)
    interactions = relationship("UserJobInteraction")
    tasks = relationship("ApplicationTask")
    notification_preferences = relationship(
        "UserNotificationPreferences", uselist=False, back_populates="user"
    )


class CandidateProfile(Base):
    """Candidate profile model"""

    __tablename__ = "candidate_profiles"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name = Column(EncryptedString)
    phone = Column(EncryptedString)
    location = Column(String)
    headline = Column(String)
    work_experience = Column(JSON)
    education = Column(JSON)
    skills = Column(JSON)
    resume_file_url = Column(String)
    parsed_at = Column(DateTime)

    # Relationships
    user = relationship("User")


class FailedLoginAttempt(Base):
    """Failed login attempt model for security tracking"""

    __tablename__ = "failed_login_attempts"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    email = Column(String, nullable=False, index=True)  # Email attempted
    ip_address = Column(String, nullable=False)
    user_agent = Column(String)
    attempted_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")


class Job(Base):
    """Job model"""

    __tablename__ = "jobs"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)
    external_id = Column(String)
    title = Column(String, nullable=False, index=True)
    company = Column(String, index=True)
    location = Column(String, index=True)
    description = Column(Text)
    raw_json = Column(JSON)
    apply_url = Column(String)
    salary_range = Column(String)
    type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interactions = relationship("UserJobInteraction")
    tasks = relationship("ApplicationTask")
    index = relationship("JobIndex", uselist=False)


class JobIndex(Base):
    """Job index model for search and matching"""

    __tablename__ = "job_index"
    __table_args__ = ({"extend_existing": True},)

    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    search_vector = Column(JSON)
    facets = Column(JSON)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job")


class UserJobInteraction(Base):
    """User-job interaction model"""

    __tablename__ = "user_job_interactions"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    action = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    interaction_metadata = Column(JSON)

    # Relationships
    user = relationship("User")
    job = relationship("Job")


class ApplicationTask(Base):
    """Application task model"""

    __tablename__ = "application_tasks"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    status = Column(String, default="queued")
    attempt_count = Column(Integer, default=0)
    last_error = Column(Text)
    assigned_worker = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    job = relationship("Job")
    audit_logs = relationship("ApplicationAuditLog")


class ApplicationAuditLog(Base):
    """Application audit log model"""

    __tablename__ = "application_audit_logs"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("application_tasks.id"), nullable=False
    )
    step = Column(String, nullable=False)
    payload = Column(JSON)
    artifacts = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("ApplicationTask")


class Domain(Base):
    """Domain configuration model for rate limiting and ATS type detection"""

    __tablename__ = "domains"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host = Column(String, unique=True, nullable=False)
    ats_type = Column(String)
    rate_limit_policy = Column(JSON)
    captcha_type = Column(String)
    last_status = Column(String)


class CoverLetterTemplate(Base):
    """Cover letter template model"""

    __tablename__ = "cover_letter_templates"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String)
    template_body = Column(Text)
    style_params = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class Notification(Base):
    """User notification model"""

    __tablename__ = "notifications"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("application_tasks.id"), nullable=True
    )
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSON)
    read = Column(Boolean, default=False)
    delivered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    task = relationship("ApplicationTask")


class UserNotificationPreferences(Base):
    """User notification preferences model"""

    __tablename__ = "user_notification_preferences"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )

    # Push notification preferences
    push_enabled = Column(Boolean, default=True)
    push_application_submitted = Column(Boolean, default=True)
    push_application_completed = Column(Boolean, default=True)
    push_application_failed = Column(Boolean, default=True)
    push_captcha_detected = Column(Boolean, default=True)
    push_job_match_found = Column(Boolean, default=True)
    push_system_notification = Column(Boolean, default=True)

    # Email notification preferences
    email_enabled = Column(Boolean, default=True)
    email_application_submitted = Column(Boolean, default=False)
    email_application_completed = Column(Boolean, default=True)
    email_application_failed = Column(Boolean, default=True)
    email_captcha_detected = Column(Boolean, default=True)
    email_job_match_found = Column(Boolean, default=True)
    email_system_notification = Column(Boolean, default=True)

    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String, default="22:00")  # HH:MM format
    quiet_hours_end = Column(String, default="08:00")  # HH:MM format

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class DeviceToken(Base):
    """Device token model for push notifications"""

    __tablename__ = "device_tokens"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id = Column(String, nullable=False)  # Unique device identifier
    platform = Column(String, nullable=False)  # 'ios' or 'android'
    token = Column(String, nullable=False, unique=True)  # APNs or FCM token
    app_version = Column(String)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="unique_user_device"),
    )


class NotificationTemplate(Base):
    """Notification template model for customizable notification content"""

    __tablename__ = "notification_templates"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)  # e.g., 'application_submitted'
    title_template = Column(
        String, nullable=False
    )  # e.g., 'Application Submitted for {{job_title}}'
    message_template = Column(
        Text, nullable=False
    )  # e.g., 'Your application for {{job_title}} at {{company}} has been submitted successfully.'
    email_html_template = Column(Text)  # HTML template for email notifications
    channels = Column(JSON, default=["push", "email"])  # Supported channels
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApiKey(Base):
    """API key model for internal service authentication"""

    __tablename__ = "api_keys"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Hashed key prefix (first 8 chars stored in plaintext for identification)
    key_prefix = Column(String(8), nullable=False, unique=True, index=True)
    key_hash = Column(String, nullable=False)  # bcrypt hash of full key
    name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    service_type = Column(
        String, nullable=False
    )  # 'ingestion', 'automation', 'analytics', 'webhook'
    permissions = Column(JSON, default=[])  # List of permission strings
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String, nullable=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User")

    __table_args__ = (UniqueConstraint("key_prefix", name="unique_key_prefix"),)


class ApiKeyUsageLog(Base):
    """API key usage log for auditing and rate limiting"""

    __tablename__ = "api_key_usage_logs"
    __table_args__ = ({"extend_existing": True},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer)
    request_size = Column(Integer)  # bytes
    response_size = Column(Integer)  # bytes
    duration_ms = Column(Integer)
    ip_address = Column(String)
    user_agent = Column(String)
    error_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    api_key = relationship("ApiKey")
