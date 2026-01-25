"""
Database Models

Defines SQLAlchemy ORM models for the application.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator
import uuid
from datetime import datetime
from backend.db.database import Base
from backend.encryption import encrypt_pii, decrypt_pii


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
    __table_args__ = (
        {"extend_existing": True},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # MFA fields
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String)
    mfa_backup_codes = Column(JSON)
    
    # Relationships
    profile = relationship("backend.db.models.CandidateProfile", uselist=False)
    interactions = relationship("backend.db.models.UserJobInteraction")
    tasks = relationship("backend.db.models.ApplicationTask")


class CandidateProfile(Base):
    """Candidate profile model"""
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        {"extend_existing": True},
    )
    
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
    user = relationship("backend.db.models.User")


class Job(Base):
    """Job model"""
    __tablename__ = "jobs"
    __table_args__ = (
        {"extend_existing": True},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)
    external_id = Column(String)
    title = Column(String, nullable=False)
    company = Column(String)
    location = Column(String)
    description = Column(Text)
    raw_json = Column(JSON)
    apply_url = Column(String)
    salary_range = Column(String)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = relationship("backend.db.models.UserJobInteraction")
    tasks = relationship("backend.db.models.ApplicationTask")
    index = relationship("backend.db.models.JobIndex", uselist=False)


class JobIndex(Base):
    """Job index model for search and matching"""
    __tablename__ = "job_index"
    __table_args__ = (
        {"extend_existing": True},
    )
    
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    search_vector = Column(JSON)
    facets = Column(JSON)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("backend.db.models.Job")


class UserJobInteraction(Base):
    """User-job interaction model"""
    __tablename__ = "user_job_interactions"
    __table_args__ = (
        {"extend_existing": True},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    action = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    interaction_metadata = Column(JSON)
    
    # Relationships
    user = relationship("backend.db.models.User")
    job = relationship("backend.db.models.Job")


class ApplicationTask(Base):
    """Application task model"""
    __tablename__ = "application_tasks"
    __table_args__ = (
        {"extend_existing": True},
    )
    
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
    user = relationship("backend.db.models.User")
    job = relationship("backend.db.models.Job")
    audit_logs = relationship("backend.db.models.ApplicationAuditLog")


class ApplicationAuditLog(Base):
    """Application audit log model"""
    __tablename__ = "application_audit_logs"
    __table_args__ = (
        {"extend_existing": True},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("application_tasks.id"), nullable=False)
    step = Column(String, nullable=False)
    payload = Column(JSON)
    artifacts = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("backend.db.models.ApplicationTask")


class Domain(Base):
    """Domain configuration model for rate limiting and ATS type detection"""
    __tablename__ = "domains"
    __table_args__ = (
        {"extend_existing": True},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host = Column(String, unique=True, nullable=False)
    ats_type = Column(String)
    rate_limit_policy = Column(JSON)
    captcha_type = Column(String)
    last_status = Column(String)


class CoverLetterTemplate(Base):
    """Cover letter template model"""
    __tablename__ = "cover_letter_templates"
    __table_args__ = (
        {"extend_existing": True},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String)
    template_body = Column(Text)
    style_params = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("backend.db.models.User")