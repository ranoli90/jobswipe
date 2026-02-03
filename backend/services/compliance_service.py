"""
GDPR and CCPA Compliance Service

This service provides comprehensive compliance functionality for GDPR (EU) and CCPA (California)
regulations including data export, deletion, consent management, and audit logging.

Key Features:
- GDPR Article 20: Right to data portability (data export)
- GDPR Article 17: Right to erasure (account deletion)
- CCPA: Right to deletion and data portability
- Granular consent management
- Data anonymization utilities
- Comprehensive audit logging
- Data retention policy enforcement
"""

import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.db.models import (
    User,
    UserJobInteraction,
    ApplicationTask,
    Notification,
    CoverLetterTemplate,
    DeviceToken,
    FailedLoginAttempt,
    UserConsent,
    DataExportRequest,
    DataDeletionRequest,
    ComplianceAuditLog,
)

# Configure logging
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


class ConsentType(str, Enum):
    """Types of user consent"""
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    MARKETING_EMAILS = "marketing_emails"
    ANALYTICS_COOKIES = "analytics_cookies"
    MARKETING_COOKIES = "marketing_cookies"
    THIRD_PARTY_SHARING = "third_party_sharing"
    DATA_PROCESSING = "data_processing"


class ConsentStatus(str, Enum):
    """Status of consent"""
    GRANTED = "granted"
    REVOKED = "revoked"
    PENDING = "pending"


class ExportStatus(str, Enum):
    """Status of data export request"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DeletionStatus(str, Enum):
    """Status of data deletion request"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComplianceAction(str, Enum):
    """Types of compliance actions for audit logging"""
    DATA_EXPORT_REQUESTED = "data_export_requested"
    DATA_EXPORT_COMPLETED = "data_export_completed"
    DATA_EXPORT_DOWNLOADED = "data_export_downloaded"
    DATA_DELETION_REQUESTED = "data_deletion_requested"
    DATA_DELETION_COMPLETED = "data_deletion_completed"
    DATA_DELETION_CANCELLED = "data_deletion_cancelled"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    CONSENT_UPDATED = "consent_updated"
    DATA_ANONYMIZED = "data_anonymized"
    RETENTION_POLICY_ENFORCED = "retention_policy_enforced"


class ComplianceService:
    """
    Service for handling GDPR and CCPA compliance operations.

    This service provides methods for:
    - Data export (right to data portability)
    - Account deletion (right to erasure)
    - Consent management
    - Data anonymization
    - Audit logging
    - Data retention enforcement
    """

    # Data retention periods (in days)
    RETENTION_PERIODS = {
        "user_data": 2555,  # 7 years for legal obligations
        "deleted_accounts": 30,  # 30 days grace period
        "export_requests": 30,  # Export files available for 30 days
        "audit_logs": 2555,  # 7 years for compliance
        "failed_login_attempts": 90,  # 90 days for security
        "session_logs": 365,  # 1 year for security
        "notification_logs": 365,  # 1 year
    }

    def __init__(self, db: Session):
        """
        Initialize the compliance service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ==================== Data Export (GDPR Article 20 / CCPA) ====================

    def request_data_export(
        self,
        user_id: uuid.UUID,
        format: str = "json",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DataExportRequest:
        """
        Request a data export for a user (GDPR Article 20 - Right to data portability).

        Args:
            user_id: UUID of the user requesting export
            format: Export format (currently only "json" supported)
            ip_address: IP address of the requester
            user_agent: User agent of the requester

        Returns:
            DataExportRequest object
        """
        # Check for existing pending export
        existing = (
            self.db.query(DataExportRequest)
            .filter(
                DataExportRequest.user_id == user_id,
                DataExportRequest.status.in_([ExportStatus.PENDING, ExportStatus.PROCESSING]),
            )
            .first()
        )

        if existing:
            logger.info("Returning existing export request %s for user %s", existing.id, user_id)
            return existing

        # Create new export request
        export_request = DataExportRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            status=ExportStatus.PENDING,
            format=format,
            requested_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.RETENTION_PERIODS["export_requests"]),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(export_request)
        self.db.commit()
        self.db.refresh(export_request)

        # Log the action
        self._log_compliance_action(
            user_id=user_id,
            action=ComplianceAction.DATA_EXPORT_REQUESTED,
            details={"export_id": str(export_request.id), "format": format},
            ip_address=ip_address,
        )

        security_logger.info(
            "Data export requested for user %s",
            user_id,
            extra={"user_id": str(user_id), "export_id": str(export_request.id)},
        )

        return export_request

    def process_data_export(self, export_request_id: uuid.UUID) -> Optional[str]:
        """
        Process a data export request and generate the export file.

        Args:
            export_request_id: UUID of the export request

        Returns:
            Path to the generated export file or None if failed
        """
        export_request = (
            self.db.query(DataExportRequest)
            .filter(DataExportRequest.id == export_request_id)
            .first()
        )

        if not export_request:
            logger.error("Export request %s not found", export_request_id)
            return None

        try:
            export_request.status = ExportStatus.PROCESSING
            self.db.commit()

            # Collect all user data
            user_data = self._collect_user_data(export_request.user_id)

            # Generate export file
            export_content = json.dumps(user_data, indent=2, default=str)
            export_request.export_data = export_content
            export_request.status = ExportStatus.COMPLETED
            export_request.completed_at = datetime.now(timezone.utc)

            self.db.commit()

            # Log completion
            self._log_compliance_action(
                user_id=export_request.user_id,
                action=ComplianceAction.DATA_EXPORT_COMPLETED,
                details={"export_id": str(export_request_id)},
            )

            logger.info("Data export %s completed successfully", export_request_id)
            return export_content

        except Exception as e:
            export_request.status = ExportStatus.FAILED
            export_request.error_message = str(e)
            self.db.commit()

            logger.error("Data export %s failed: %s", export_request_id, e)
            return None

    def _collect_user_data(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Collect all user data for export.

        Args:
            user_id: UUID of the user

        Returns:
            Dictionary containing all user data
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Collect data from all related tables
        data = {
            "export_metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "user_id": str(user_id),
                "export_version": "1.0",
                "regulations": ["GDPR", "CCPA"],
            },
            "user_account": {
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "email_verified": user.email_verified,
                "mfa_enabled": user.mfa_enabled,
                "status": user.status,
            },
            "profile": None,
            "job_interactions": [],
            "applications": [],
            "notifications": [],
            "cover_letters": [],
            "device_tokens": [],
            "notification_preferences": None,
            "consent_history": [],
            "login_history": [],
        }

        # Profile data
        if user.profile:
            data["profile"] = {
                "full_name": user.profile.full_name,
                "phone": user.profile.phone,
                "location": user.profile.location,
                "headline": user.profile.headline,
                "work_experience": user.profile.work_experience,
                "education": user.profile.education,
                "skills": user.profile.skills,
                "resume_file_url": user.profile.resume_file_url,
                "parsed_at": user.profile.parsed_at.isoformat() if user.profile.parsed_at else None,
            }

        # Job interactions
        interactions = (
            self.db.query(UserJobInteraction)
            .filter(UserJobInteraction.user_id == user_id)
            .all()
        )
        for interaction in interactions:
            data["job_interactions"].append({
                "id": str(interaction.id),
                "job_id": str(interaction.job_id),
                "action": interaction.action,
                "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                "metadata": interaction.interaction_metadata,
            })

        # Application tasks
        tasks = (
            self.db.query(ApplicationTask)
            .filter(ApplicationTask.user_id == user_id)
            .all()
        )
        for task in tasks:
            task_data = {
                "id": str(task.id),
                "job_id": str(task.job_id),
                "status": task.status,
                "attempt_count": task.attempt_count,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            data["applications"].append(task_data)

        # Notifications
        notifications = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .all()
        )
        for notification in notifications:
            data["notifications"].append({
                "id": str(notification.id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "read": notification.read,
                "delivered": notification.delivered,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
            })

        # Cover letter templates
        templates = (
            self.db.query(CoverLetterTemplate)
            .filter(CoverLetterTemplate.user_id == user_id)
            .all()
        )
        for template in templates:
            data["cover_letters"].append({
                "id": str(template.id),
                "title": template.title,
                "template_body": template.template_body,
                "style_params": template.style_params,
                "created_at": template.created_at.isoformat() if template.created_at else None,
            })

        # Device tokens
        devices = (
            self.db.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id)
            .all()
        )
        for device in devices:
            data["device_tokens"].append({
                "id": str(device.id),
                "device_id": device.device_id,
                "platform": device.platform,
                "app_version": device.app_version,
                "last_used": device.last_used.isoformat() if device.last_used else None,
                "created_at": device.created_at.isoformat() if device.created_at else None,
            })

        # Notification preferences
        if user.notification_preferences:
            prefs = user.notification_preferences
            data["notification_preferences"] = {
                "push_enabled": prefs.push_enabled,
                "push_application_submitted": prefs.push_application_submitted,
                "push_application_completed": prefs.push_application_completed,
                "push_application_failed": prefs.push_application_failed,
                "push_captcha_detected": prefs.push_captcha_detected,
                "push_job_match_found": prefs.push_job_match_found,
                "push_system_notification": prefs.push_system_notification,
                "email_enabled": prefs.email_enabled,
                "email_application_submitted": prefs.email_application_submitted,
                "email_application_completed": prefs.email_application_completed,
                "email_application_failed": prefs.email_application_failed,
                "email_captcha_detected": prefs.email_captcha_detected,
                "email_job_match_found": prefs.email_job_match_found,
                "email_system_notification": prefs.email_system_notification,
                "quiet_hours_enabled": prefs.quiet_hours_enabled,
                "quiet_hours_start": prefs.quiet_hours_start,
                "quiet_hours_end": prefs.quiet_hours_end,
            }

        # Consent history
        consents = (
            self.db.query(UserConsent)
            .filter(UserConsent.user_id == user_id)
            .order_by(UserConsent.created_at.desc())
            .all()
        )
        for consent in consents:
            data["consent_history"].append({
                "id": str(consent.id),
                "consent_type": consent.consent_type,
                "status": consent.status,
                "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
                "ip_address": consent.ip_address,
                "user_agent": consent.user_agent,
            })

        # Login history (failed attempts)
        login_attempts = (
            self.db.query(FailedLoginAttempt)
            .filter(FailedLoginAttempt.user_id == user_id)
            .order_by(FailedLoginAttempt.attempted_at.desc())
            .limit(100)  # Limit to last 100 attempts
            .all()
        )
        for attempt in login_attempts:
            data["login_history"].append({
                "id": str(attempt.id),
                "attempted_at": attempt.attempted_at.isoformat() if attempt.attempted_at else None,
                "ip_address": attempt.ip_address,
                "user_agent": attempt.user_agent,
            })

        return data

    def get_export_download(self, export_request_id: uuid.UUID, user_id: uuid.UUID) -> Optional[str]:
        """
        Get the download URL/content for a completed export.

        Args:
            export_request_id: UUID of the export request
            user_id: UUID of the user (for verification)

        Returns:
            Export data as JSON string or None if not available
        """
        export_request = (
            self.db.query(DataExportRequest)
            .filter(
                DataExportRequest.id == export_request_id,
                DataExportRequest.user_id == user_id,
            )
            .first()
        )

        if not export_request or export_request.status != ExportStatus.COMPLETED:
            return None

        # Check if export has expired
        if export_request.expires_at and export_request.expires_at < datetime.now(timezone.utc):
            export_request.status = ExportStatus.EXPIRED
            self.db.commit()
            return None

        # Log download
        self._log_compliance_action(
            user_id=user_id,
            action=ComplianceAction.DATA_EXPORT_DOWNLOADED,
            details={"export_id": str(export_request_id)},
        )

        return export_request.export_data

    # ==================== Data Deletion (GDPR Article 17 / CCPA) ====================

    def request_data_deletion(
        self,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DataDeletionRequest:
        """
        Request account deletion (GDPR Article 17 - Right to erasure / CCPA deletion right).

        The deletion is performed as anonymization to maintain referential integrity
        while removing all PII.

        Args:
            user_id: UUID of the user requesting deletion
            reason: Optional reason for deletion
            ip_address: IP address of the requester
            user_agent: User agent of the requester

        Returns:
            DataDeletionRequest object
        """
        # Check for existing pending deletion
        existing = (
            self.db.query(DataDeletionRequest)
            .filter(
                DataDeletionRequest.user_id == user_id,
                DataDeletionRequest.status.in_([DeletionStatus.PENDING, DeletionStatus.PROCESSING]),
            )
            .first()
        )

        if existing:
            logger.info("Returning existing deletion request %s for user %s", existing.id, user_id)
            return existing

        # Create new deletion request
        deletion_request = DataDeletionRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            status=DeletionStatus.PENDING,
            reason=reason,
            requested_at=datetime.now(timezone.utc),
            grace_period_end=datetime.now(timezone.utc) + timedelta(days=self.RETENTION_PERIODS["deleted_accounts"]),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(deletion_request)
        self.db.commit()
        self.db.refresh(deletion_request)

        # Log the action
        self._log_compliance_action(
            user_id=user_id,
            action=ComplianceAction.DATA_DELETION_REQUESTED,
            details={"deletion_id": str(deletion_request.id), "reason": reason},
            ip_address=ip_address,
        )

        security_logger.info(
            "Data deletion requested for user %s",
            user_id,
            extra={"user_id": str(user_id), "deletion_id": str(deletion_request.id)},
        )

        return deletion_request

    def process_data_deletion(self, deletion_request_id: uuid.UUID) -> bool:
        """
        Process a data deletion request by anonymizing user data.

        This method anonymizes rather than hard-deletes data to maintain
        referential integrity while removing all PII.

        Args:
            deletion_request_id: UUID of the deletion request

        Returns:
            True if successful, False otherwise
        """
        deletion_request = (
            self.db.query(DataDeletionRequest)
            .filter(DataDeletionRequest.id == deletion_request_id)
            .first()
        )

        if not deletion_request:
            logger.error("Deletion request %s not found", deletion_request_id)
            return False

        try:
            deletion_request.status = DeletionStatus.PROCESSING
            self.db.commit()

            user_id = deletion_request.user_id

            # Anonymize user data
            self._anonymize_user_data(user_id)

            deletion_request.status = DeletionStatus.COMPLETED
            deletion_request.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            # Log completion
            self._log_compliance_action(
                user_id=user_id,
                action=ComplianceAction.DATA_DELETION_COMPLETED,
                details={"deletion_id": str(deletion_request_id)},
            )

            security_logger.info(
                "Data deletion completed for user %s",
                user_id,
                extra={"user_id": str(user_id), "deletion_id": str(deletion_request_id)},
            )

            return True

        except Exception as e:
            deletion_request.status = DeletionStatus.FAILED
            deletion_request.error_message = str(e)
            self.db.commit()

            logger.error("Data deletion %s failed: %s", deletion_request_id, e)
            return False

    def _anonymize_user_data(self, user_id: uuid.UUID) -> None:
        """
        Anonymize all user data while maintaining referential integrity.

        Args:
            user_id: UUID of the user to anonymize
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Generate anonymous identifier
        anonymous_id = f"deleted_{secrets.token_hex(16)}"

        # Anonymize user account
        user.email = f"{anonymous_id}@deleted.jobswipe"
        user.password_hash = "deleted"
        user.status = "deleted"
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        user.lockout_until = None

        # Anonymize profile
        if user.profile:
            profile = user.profile
            profile.full_name = "Deleted User"
            profile.phone = None
            profile.location = None
            profile.headline = None
            profile.work_experience = None
            profile.education = None
            profile.skills = None
            profile.resume_file_url = None

        # Delete device tokens
        self.db.query(DeviceToken).filter(DeviceToken.user_id == user_id).delete()

        # Delete cover letter templates
        self.db.query(CoverLetterTemplate).filter(CoverLetterTemplate.user_id == user_id).delete()

        # Anonymize notifications (keep for analytics but remove PII)
        notifications = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .all()
        )
        for notification in notifications:
            notification.message = "[Content removed for privacy]"
            notification.data = None

        self.db.commit()

        # Log anonymization
        self._log_compliance_action(
            user_id=user_id,
            action=ComplianceAction.DATA_ANONYMIZED,
            details={"anonymous_id": anonymous_id},
        )

    def cancel_deletion_request(self, deletion_request_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Cancel a pending deletion request during the grace period.

        Args:
            deletion_request_id: UUID of the deletion request
            user_id: UUID of the user (for verification)

        Returns:
            True if cancelled, False otherwise
        """
        deletion_request = (
            self.db.query(DataDeletionRequest)
            .filter(
                DataDeletionRequest.id == deletion_request_id,
                DataDeletionRequest.user_id == user_id,
                DataDeletionRequest.status == DeletionStatus.PENDING,
            )
            .first()
        )

        if not deletion_request:
            return False

        deletion_request.status = DeletionStatus.COMPLETED  # Mark as completed (cancelled)
        deletion_request.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        self._log_compliance_action(
            user_id=user_id,
            action=ComplianceAction.DATA_DELETION_CANCELLED,
            details={"deletion_id": str(deletion_request_id)},
        )

        return True

    # ==================== Consent Management ====================

    def get_user_consents(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get all current consent status for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Dictionary of consent types and their status
        """
        consents = (
            self.db.query(UserConsent)
            .filter(UserConsent.user_id == user_id)
            .order_by(UserConsent.created_at.desc())
            .all()
        )

        # Get latest status for each consent type
        consent_map = {}
        for consent in consents:
            if consent.consent_type not in consent_map:
                consent_map[consent.consent_type] = {
                    "status": consent.status,
                    "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                    "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
                    "version": consent.consent_version,
                }

        # Ensure all consent types are present
        for consent_type in ConsentType:
            if consent_type.value not in consent_map:
                consent_map[consent_type.value] = {
                    "status": ConsentStatus.PENDING,
                    "granted_at": None,
                    "revoked_at": None,
                    "version": None,
                }

        return consent_map

    def update_consent(
        self,
        user_id: uuid.UUID,
        consent_type: ConsentType,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_version: str = "1.0",
    ) -> UserConsent:
        """
        Update a specific consent for a user.

        Args:
            user_id: UUID of the user
            consent_type: Type of consent being updated
            granted: True to grant, False to revoke
            ip_address: IP address of the requester
            user_agent: User agent of the requester
            consent_version: Version of the consent terms

        Returns:
            UserConsent object
        """
        # Create new consent record
        consent = UserConsent(
            id=uuid.uuid4(),
            user_id=user_id,
            consent_type=consent_type.value,
            status=ConsentStatus.GRANTED if granted else ConsentStatus.REVOKED,
            granted_at=datetime.now(timezone.utc) if granted else None,
            revoked_at=datetime.now(timezone.utc) if not granted else None,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_version=consent_version,
        )

        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)

        # Log the action
        action = ComplianceAction.CONSENT_GRANTED if granted else ComplianceAction.CONSENT_REVOKED
        self._log_compliance_action(
            user_id=user_id,
            action=action,
            details={"consent_type": consent_type.value, "version": consent_version},
            ip_address=ip_address,
        )

        return consent

    def has_consent(self, user_id: uuid.UUID, consent_type: ConsentType) -> bool:
        """
        Check if a user has granted a specific consent.

        Args:
            user_id: UUID of the user
            consent_type: Type of consent to check

        Returns:
            True if consent is granted, False otherwise
        """
        latest_consent = (
            self.db.query(UserConsent)
            .filter(
                UserConsent.user_id == user_id,
                UserConsent.consent_type == consent_type.value,
            )
            .order_by(UserConsent.created_at.desc())
            .first()
        )

        if not latest_consent:
            return False

        return latest_consent.status == ConsentStatus.GRANTED

    # ==================== Audit Logging ====================

    def _log_compliance_action(
        self,
        user_id: uuid.UUID,
        action: ComplianceAction,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> ComplianceAuditLog:
        """
        Log a compliance-related action.

        Args:
            user_id: UUID of the user
            action: Type of compliance action
            details: Additional details
            ip_address: IP address of the requester

        Returns:
            ComplianceAuditLog object
        """
        log_entry = ComplianceAuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action.value,
            details=details or {},
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(log_entry)
        self.db.commit()

        return log_entry

    def get_audit_logs(
        self,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[ComplianceAuditLog]:
        """
        Get compliance audit logs with optional filtering.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results

        Returns:
            List of ComplianceAuditLog objects
        """
        query = self.db.query(ComplianceAuditLog)

        if user_id:
            query = query.filter(ComplianceAuditLog.user_id == user_id)

        if action:
            query = query.filter(ComplianceAuditLog.action == action)

        if start_date:
            query = query.filter(ComplianceAuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(ComplianceAuditLog.created_at <= end_date)

        return query.order_by(ComplianceAuditLog.created_at.desc()).limit(limit).all()

    # ==================== Data Retention Enforcement ====================

    def enforce_retention_policies(self) -> Dict[str, int]:
        """
        Enforce data retention policies by deleting expired data.

        Returns:
            Dictionary with counts of deleted records by type
        """
        deleted_counts = {
            "export_requests": 0,
            "audit_logs": 0,
            "failed_login_attempts": 0,
        }

        # Delete expired export requests
        export_cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_PERIODS["export_requests"])
        expired_exports = (
            self.db.query(DataExportRequest)
            .filter(
                DataExportRequest.status == ExportStatus.COMPLETED,
                DataExportRequest.completed_at < export_cutoff,
            )
            .all()
        )
        for export in expired_exports:
            export.export_data = None  # Remove the actual data
            export.status = ExportStatus.EXPIRED
            deleted_counts["export_requests"] += 1

        # Delete old audit logs
        audit_cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_PERIODS["audit_logs"])
        deleted_counts["audit_logs"] = (
            self.db.query(ComplianceAuditLog)
            .filter(ComplianceAuditLog.created_at < audit_cutoff)
            .delete(synchronize_session=False)
        )

        # Delete old failed login attempts
        login_cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_PERIODS["failed_login_attempts"])
        deleted_counts["failed_login_attempts"] = (
            self.db.query(FailedLoginAttempt)
            .filter(FailedLoginAttempt.attempted_at < login_cutoff)
            .delete(synchronize_session=False)
        )

        self.db.commit()

        # Log retention enforcement
        self._log_compliance_action(
            user_id=None,
            action=ComplianceAction.RETENTION_POLICY_ENFORCED,
            details=deleted_counts,
        )

        logger.info("Retention policies enforced: %s", deleted_counts)

        return deleted_counts

    # ==================== Privacy Policy and Data Retention Info ====================

    def get_privacy_policy_info(self) -> Dict[str, Any]:
        """
        Get privacy policy information.

        Returns:
            Dictionary with privacy policy details
        """
        return {
            "version": "1.0",
            "last_updated": "2026-01-01",
            "contact_email": "privacy@jobswipe.com",
            "data_controller": {
                "name": "JobSwipe Inc.",
                "address": "123 Privacy Lane, Tech City, TC 12345",
                "email": "privacy@jobswipe.com",
            },
            "legal_bases": [
                {
                    "basis": "Consent",
                    "purposes": ["Marketing communications", "Analytics cookies", "Third-party sharing"],
                },
                {
                    "basis": "Contract",
                    "purposes": ["Account management", "Job application processing", "Service delivery"],
                },
                {
                    "basis": "Legal Obligation",
                    "purposes": ["Tax records", "Fraud prevention", "Regulatory compliance"],
                },
                {
                    "basis": "Legitimate Interest",
                    "purposes": ["Service improvement", "Security", "Customer support"],
                },
            ],
            "user_rights": {
                "gdpr": [
                    "Right to access",
                    "Right to rectification",
                    "Right to erasure (right to be forgotten)",
                    "Right to restrict processing",
                    "Right to data portability",
                    "Right to object",
                    "Rights related to automated decision-making",
                ],
                "ccpa": [
                    "Right to know",
                    "Right to delete",
                    "Right to opt-out of sale",
                    "Right to non-discrimination",
                ],
            },
            "cookies": {
                "essential": ["session", "csrf", "auth"],
                "analytics": ["google_analytics", "mixpanel"],
                "marketing": ["facebook_pixel", "google_ads"],
            },
        }

    def get_data_retention_info(self) -> Dict[str, Any]:
        """
        Get data retention policy information.

        Returns:
            Dictionary with retention policy details
        """
        return {
            "version": "1.0",
            "last_updated": "2026-01-01",
            "retention_periods": {
                "account_data": {
                    "period": "7 years",
                    "days": self.RETENTION_PERIODS["user_data"],
                    "legal_basis": "Legal obligation (tax and regulatory compliance)",
                    "description": "Account data is retained for 7 years after account closure for legal compliance.",
                },
                "deleted_accounts": {
                    "period": "30 days",
                    "days": self.RETENTION_PERIODS["deleted_accounts"],
                    "legal_basis": "Legitimate interest (grace period for account recovery)",
                    "description": "Deleted accounts remain in a grace period for 30 days before permanent anonymization.",
                },
                "export_requests": {
                    "period": "30 days",
                    "days": self.RETENTION_PERIODS["export_requests"],
                    "legal_basis": "Consent",
                    "description": "Data export files are available for download for 30 days.",
                },
                "audit_logs": {
                    "period": "7 years",
                    "days": self.RETENTION_PERIODS["audit_logs"],
                    "legal_basis": "Legal obligation (compliance and security)",
                    "description": "Audit logs are retained for 7 years for compliance and security purposes.",
                },
                "failed_login_attempts": {
                    "period": "90 days",
                    "days": self.RETENTION_PERIODS["failed_login_attempts"],
                    "legal_basis": "Legitimate interest (security)",
                    "description": "Failed login attempts are retained for 90 days for security monitoring.",
                },
                "session_logs": {
                    "period": "1 year",
                    "days": self.RETENTION_PERIODS["session_logs"],
                    "legal_basis": "Legitimate interest (security and fraud prevention)",
                    "description": "Session logs are retained for 1 year for security and fraud prevention.",
                },
                "notification_logs": {
                    "period": "1 year",
                    "days": self.RETENTION_PERIODS["notification_logs"],
                    "legal_basis": "Legitimate interest (service improvement)",
                    "description": "Notification delivery logs are retained for 1 year.",
                },
            },
            "automatic_deletion": True,
            "deletion_schedule": "Daily at 00:00 UTC",
        }


# Singleton instance for dependency injection
_compliance_service: Optional[ComplianceService] = None


def get_compliance_service(db: Session) -> ComplianceService:
    """
    Get or create a compliance service instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        ComplianceService instance
    """
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceService(db)
    else:
        _compliance_service.db = db
    return _compliance_service
