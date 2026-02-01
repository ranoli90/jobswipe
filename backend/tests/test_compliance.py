"""
Compliance Tests

Unit and integration tests for GDPR and CCPA compliance features including:
- Data export functionality
- Data deletion (anonymization)
- Consent management
- Audit logging
- Data retention enforcement
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.db.models import (
    User,
    CandidateProfile,
    UserJobInteraction,
    ApplicationTask,
    Notification,
    UserConsent,
    DataExportRequest,
    DataDeletionRequest,
    ComplianceAuditLog,
    CookieConsent,
)
from backend.services.compliance_service import (
    ComplianceService,
    ConsentType,
    ConsentStatus,
    ExportStatus,
    DeletionStatus,
    ComplianceAction,
    get_compliance_service,
)


# ==================== Fixtures ====================

@pytest.fixture
def compliance_service(db_session: Session) -> ComplianceService:
    """Create a compliance service instance for testing"""
    return ComplianceService(db_session)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        status="active",
        created_at=datetime.utcnow(),
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_user_with_profile(db_session: Session, test_user: User) -> User:
    """Create a test user with a complete profile"""
    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Test User",
        phone="+1234567890",
        location="San Francisco, CA",
        headline="Software Engineer",
        work_experience=[
            {
                "company": "Tech Corp",
                "title": "Senior Engineer",
                "start_date": "2020-01",
                "end_date": "2023-12",
            }
        ],
        education=[
            {
                "school": "University of Test",
                "degree": "B.S. Computer Science",
                "graduation_year": 2019,
            }
        ],
        skills=["Python", "FastAPI", "PostgreSQL"],
    )
    db_session.add(profile)
    db_session.commit()
    return test_user


@pytest.fixture
def test_user_with_interactions(db_session: Session, test_user: User) -> User:
    """Create a test user with job interactions"""
    from backend.db.models import Job
    
    # Create a test job
    job = Job(
        id=uuid.uuid4(),
        source="test",
        title="Test Job",
        company="Test Company",
        description="Test job description",
        created_at=datetime.utcnow(),
    )
    db_session.add(job)
    db_session.commit()
    
    # Create interactions
    interaction = UserJobInteraction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        job_id=job.id,
        action="viewed",
        created_at=datetime.utcnow(),
        interaction_metadata={"source": "search"},
    )
    db_session.add(interaction)
    db_session.commit()
    
    return test_user


# ==================== Data Export Tests ====================

class TestDataExport:
    """Tests for data export functionality (GDPR Article 20)"""
    
    def test_request_data_export_creates_request(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that requesting data export creates a new export request"""
        export_request = compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
            ip_address="127.0.0.1",
        )
        
        assert export_request is not None
        assert export_request.user_id == test_user.id
        assert export_request.status == ExportStatus.PENDING
        assert export_request.format == "json"
        assert export_request.ip_address == "127.0.0.1"
    
    def test_request_data_export_returns_existing_pending(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that requesting export when one is pending returns existing"""
        # Create first request
        first_request = compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
        )
        
        # Create second request
        second_request = compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
        )
        
        assert first_request.id == second_request.id
    
    def test_process_data_export_completes_request(
        self,
        compliance_service: ComplianceService,
        test_user_with_profile: User,
        db_session: Session,
    ):
        """Test that processing export completes the request"""
        # Create export request
        export_request = compliance_service.request_data_export(
            user_id=test_user_with_profile.id,
            format="json",
        )
        
        # Process the export
        result = compliance_service.process_data_export(export_request.id)
        
        assert result is not None
        
        # Refresh from database
        db_session.refresh(export_request)
        assert export_request.status == ExportStatus.COMPLETED
        assert export_request.completed_at is not None
        assert export_request.export_data is not None
    
    def test_process_data_export_includes_all_data(
        self,
        compliance_service: ComplianceService,
        test_user_with_profile: User,
        db_session: Session,
    ):
        """Test that export includes all user data categories"""
        # Create export request
        export_request = compliance_service.request_data_export(
            user_id=test_user_with_profile.id,
            format="json",
        )
        
        # Process the export
        export_data = compliance_service.process_data_export(export_request.id)
        data = json.loads(export_data)
        
        # Check all expected keys are present
        assert "export_metadata" in data
        assert "user_account" in data
        assert "profile" in data
        assert "job_interactions" in data
        assert "applications" in data
        assert "notifications" in data
        assert "cover_letters" in data
        assert "device_tokens" in data
        assert "notification_preferences" in data
        assert "consent_history" in data
        assert "login_history" in data
    
    def test_get_export_download_returns_data(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that get_export_download returns the export data"""
        # Create and process export
        export_request = compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
        )
        compliance_service.process_data_export(export_request.id)
        
        # Get download
        data = compliance_service.get_export_download(export_request.id, test_user.id)
        
        assert data is not None
        assert isinstance(data, str)
    
    def test_get_export_download_returns_none_for_expired(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that get_export_download returns None for expired exports"""
        # Create export request with past expiration
        export_request = compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
        )
        export_request.expires_at = datetime.utcnow() - timedelta(days=1)
        export_request.status = ExportStatus.COMPLETED
        db_session.commit()
        
        # Get download should return None
        data = compliance_service.get_export_download(export_request.id, test_user.id)
        
        assert data is None


# ==================== Data Deletion Tests ====================

class TestDataDeletion:
    """Tests for data deletion functionality (GDPR Article 17 / CCPA)"""
    
    def test_request_data_deletion_creates_request(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that requesting deletion creates a new deletion request"""
        deletion_request = compliance_service.request_data_deletion(
            user_id=test_user.id,
            reason="No longer need service",
            ip_address="127.0.0.1",
        )
        
        assert deletion_request is not None
        assert deletion_request.user_id == test_user.id
        assert deletion_request.status == DeletionStatus.PENDING
        assert deletion_request.reason == "No longer need service"
        assert deletion_request.grace_period_end is not None
    
    def test_request_data_deletion_returns_existing_pending(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that requesting deletion when one is pending returns existing"""
        first_request = compliance_service.request_data_deletion(
            user_id=test_user.id,
        )
        
        second_request = compliance_service.request_data_deletion(
            user_id=test_user.id,
        )
        
        assert first_request.id == second_request.id
    
    def test_process_data_deletion_anonymizes_user(
        self,
        compliance_service: ComplianceService,
        test_user_with_profile: User,
        db_session: Session,
    ):
        """Test that deletion anonymizes user data"""
        original_email = test_user_with_profile.email
        
        # Create deletion request
        deletion_request = compliance_service.request_data_deletion(
            user_id=test_user_with_profile.id,
        )
        
        # Process deletion
        success = compliance_service.process_data_deletion(deletion_request.id)
        
        assert success is True
        
        # Refresh user from database
        db_session.refresh(test_user_with_profile)
        assert test_user_with_profile.status == "deleted"
        assert test_user_with_profile.email != original_email
        assert "@deleted.jobswipe" in test_user_with_profile.email
    
    def test_process_data_deletion_anonymizes_profile(
        self,
        compliance_service: ComplianceService,
        test_user_with_profile: User,
        db_session: Session,
    ):
        """Test that deletion anonymizes profile data"""
        # Create deletion request
        deletion_request = compliance_service.request_data_deletion(
            user_id=test_user_with_profile.id,
        )
        
        # Process deletion
        compliance_service.process_data_deletion(deletion_request.id)
        
        # Refresh profile from database
        db_session.refresh(test_user_with_profile.profile)
        profile = test_user_with_profile.profile
        
        assert profile.full_name == "Deleted User"
        assert profile.phone is None
        assert profile.work_experience is None
        assert profile.education is None
    
    def test_cancel_deletion_request_cancels_pending(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that cancellation works during grace period"""
        # Create deletion request
        deletion_request = compliance_service.request_data_deletion(
            user_id=test_user.id,
        )
        
        # Cancel the request
        success = compliance_service.cancel_deletion_request(
            deletion_request_id=deletion_request.id,
            user_id=test_user.id,
        )
        
        assert success is True
        
        # Refresh from database
        db_session.refresh(deletion_request)
        assert deletion_request.status == DeletionStatus.COMPLETED


# ==================== Consent Management Tests ====================

class TestConsentManagement:
    """Tests for consent management functionality"""
    
    def test_get_user_consents_returns_all_types(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that get_user_consents returns all consent types"""
        consents = compliance_service.get_user_consents(test_user.id)
        
        # Should include all consent types
        for consent_type in ConsentType:
            assert consent_type.value in consents
    
    def test_update_consent_creates_record(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that updating consent creates a consent record"""
        consent = compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
            granted=True,
            ip_address="127.0.0.1",
        )
        
        assert consent is not None
        assert consent.user_id == test_user.id
        assert consent.consent_type == ConsentType.MARKETING_EMAILS.value
        assert consent.status == ConsentStatus.GRANTED
        assert consent.granted_at is not None
    
    def test_update_consent_revokes_consent(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that updating consent can revoke previously granted consent"""
        # Grant consent first
        compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.ANALYTICS_COOKIES,
            granted=True,
        )
        
        # Revoke consent
        consent = compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.ANALYTICS_COOKIES,
            granted=False,
        )
        
        assert consent.status == ConsentStatus.REVOKED
        assert consent.revoked_at is not None
    
    def test_has_consent_returns_true_when_granted(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that has_consent returns True when consent is granted"""
        # Grant consent
        compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
            granted=True,
        )
        
        # Check consent
        has_consent = compliance_service.has_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
        )
        
        assert has_consent is True
    
    def test_has_consent_returns_false_when_revoked(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that has_consent returns False when consent is revoked"""
        # Grant then revoke consent
        compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
            granted=True,
        )
        compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
            granted=False,
        )
        
        # Check consent
        has_consent = compliance_service.has_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
        )
        
        assert has_consent is False
    
    def test_has_consent_returns_false_when_no_record(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that has_consent returns False when no consent record exists"""
        has_consent = compliance_service.has_consent(
            user_id=test_user.id,
            consent_type=ConsentType.THIRD_PARTY_SHARING,
        )
        
        assert has_consent is False


# ==================== Audit Logging Tests ====================

class TestAuditLogging:
    """Tests for compliance audit logging"""
    
    def test_export_request_creates_audit_log(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that requesting export creates an audit log entry"""
        compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
        )
        
        # Check audit log
        logs = compliance_service.get_audit_logs(user_id=test_user.id)
        
        assert len(logs) > 0
        assert any(log.action == ComplianceAction.DATA_EXPORT_REQUESTED.value for log in logs)
    
    def test_deletion_request_creates_audit_log(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that requesting deletion creates an audit log entry"""
        compliance_service.request_data_deletion(
            user_id=test_user.id,
        )
        
        # Check audit log
        logs = compliance_service.get_audit_logs(user_id=test_user.id)
        
        assert any(log.action == ComplianceAction.DATA_DELETION_REQUESTED.value for log in logs)
    
    def test_consent_update_creates_audit_log(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that updating consent creates an audit log entry"""
        compliance_service.update_consent(
            user_id=test_user.id,
            consent_type=ConsentType.MARKETING_EMAILS,
            granted=True,
        )
        
        # Check audit log
        logs = compliance_service.get_audit_logs(user_id=test_user.id)
        
        assert any(log.action == ComplianceAction.CONSENT_GRANTED.value for log in logs)
    
    def test_get_audit_logs_filters_by_user(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that get_audit_logs filters by user ID"""
        # Create a log for test_user
        compliance_service._log_compliance_action(
            user_id=test_user.id,
            action=ComplianceAction.DATA_EXPORT_REQUESTED,
        )
        
        # Get logs for different user
        different_user_id = uuid.uuid4()
        logs = compliance_service.get_audit_logs(user_id=different_user_id)
        
        assert len(logs) == 0


# ==================== Data Retention Tests ====================

class TestDataRetention:
    """Tests for data retention policy enforcement"""
    
    def test_enforce_retention_deletes_expired_exports(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that retention enforcement deletes expired export data"""
        # Create an old completed export
        old_export = DataExportRequest(
            id=uuid.uuid4(),
            user_id=test_user.id,
            status=ExportStatus.COMPLETED,
            format="json",
            export_data='{"test": "data"}',
            requested_at=datetime.utcnow() - timedelta(days=60),
            completed_at=datetime.utcnow() - timedelta(days=60),
        )
        db_session.add(old_export)
        db_session.commit()
        
        # Enforce retention
        counts = compliance_service.enforce_retention_policies()
        
        # Refresh from database
        db_session.refresh(old_export)
        assert old_export.export_data is None
        assert old_export.status == ExportStatus.EXPIRED
    
    def test_enforce_retention_deletes_old_audit_logs(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that retention enforcement deletes old audit logs"""
        # Create an old audit log
        old_log = ComplianceAuditLog(
            id=uuid.uuid4(),
            user_id=test_user.id,
            action=ComplianceAction.DATA_EXPORT_REQUESTED.value,
            created_at=datetime.utcnow() - timedelta(days=3000),  # Very old
        )
        db_session.add(old_log)
        db_session.commit()
        
        # Enforce retention
        counts = compliance_service.enforce_retention_policies()
        
        # Check that old log was deleted
        assert counts["audit_logs"] > 0
    
    def test_enforce_retention_deletes_old_login_attempts(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that retention enforcement deletes old failed login attempts"""
        from backend.db.models import FailedLoginAttempt
        
        # Create an old login attempt
        old_attempt = FailedLoginAttempt(
            id=uuid.uuid4(),
            user_id=test_user.id,
            email=test_user.email,
            ip_address="127.0.0.1",
            attempted_at=datetime.utcnow() - timedelta(days=100),
        )
        db_session.add(old_attempt)
        db_session.commit()
        
        # Enforce retention
        counts = compliance_service.enforce_retention_policies()
        
        # Check that old attempt was deleted
        assert counts["failed_login_attempts"] > 0


# ==================== API Endpoint Tests ====================

class TestComplianceAPI:
    """Integration tests for compliance API endpoints"""
    
    def test_get_privacy_policy_info(self, client: TestClient):
        """Test GET /compliance/privacy-policy endpoint"""
        response = client.get("/api/v1/compliance/privacy-policy")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "legal_bases" in data
        assert "user_rights" in data
    
    def test_get_data_retention_info(self, client: TestClient):
        """Test GET /compliance/data-retention endpoint"""
        response = client.get("/api/v1/compliance/data-retention")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "retention_periods" in data
    
    def test_get_consent_status_requires_auth(self, client: TestClient):
        """Test that GET /compliance/consent requires authentication"""
        response = client.get("/api/v1/compliance/consent")
        
        assert response.status_code == 401
    
    def test_update_consent_requires_auth(self, client: TestClient):
        """Test that POST /compliance/consent requires authentication"""
        response = client.post(
            "/api/v1/compliance/consent",
            json={"consent_type": "marketing_emails", "granted": True},
        )
        
        assert response.status_code == 401
    
    def test_request_export_requires_auth(self, client: TestClient):
        """Test that POST /compliance/export/request requires authentication"""
        response = client.post("/api/v1/compliance/export/request")
        
        assert response.status_code == 401
    
    def test_request_deletion_requires_auth(self, client: TestClient):
        """Test that POST /compliance/deletion/request requires authentication"""
        response = client.post("/api/v1/compliance/deletion/request")
        
        assert response.status_code == 401


# ==================== Privacy Policy and Data Retention Info Tests ====================

class TestPrivacyInfo:
    """Tests for privacy policy and data retention information"""
    
    def test_get_privacy_policy_info_structure(
        self,
        compliance_service: ComplianceService,
    ):
        """Test that privacy policy info has correct structure"""
        info = compliance_service.get_privacy_policy_info()
        
        assert "version" in info
        assert "last_updated" in info
        assert "contact_email" in info
        assert "data_controller" in info
        assert "legal_bases" in info
        assert "user_rights" in info
        assert "gdpr" in info["user_rights"]
        assert "ccpa" in info["user_rights"]
        assert "cookies" in info
    
    def test_get_data_retention_info_structure(
        self,
        compliance_service: ComplianceService,
    ):
        """Test that data retention info has correct structure"""
        info = compliance_service.get_data_retention_info()
        
        assert "version" in info
        assert "last_updated" in info
        assert "retention_periods" in info
        assert "automatic_deletion" in info
        assert "deletion_schedule" in info
        
        # Check retention periods
        periods = info["retention_periods"]
        assert "account_data" in periods
        assert "deleted_accounts" in periods
        assert "export_requests" in periods
        assert "audit_logs" in periods


# ==================== Cookie Consent Middleware Tests ====================

class TestCookieConsentMiddleware:
    """Tests for cookie consent middleware"""
    
    def test_essential_cookies_always_allowed(self):
        """Test that essential cookies are always allowed"""
        from backend.api.middleware.cookie_consent import CookieConsentMiddleware
        
        middleware = CookieConsentMiddleware(MagicMock())
        consent = {"essential": True, "analytics": False, "marketing": False}
        
        for cookie in middleware.ESSENTIAL_COOKIES:
            if not cookie.endswith("*"):
                assert middleware._is_cookie_allowed(cookie, consent) is True
    
    def test_analytics_cookies_blocked_without_consent(self):
        """Test that analytics cookies are blocked without consent"""
        from backend.api.middleware.cookie_consent import CookieConsentMiddleware
        
        middleware = CookieConsentMiddleware(MagicMock())
        consent = {"essential": True, "analytics": False, "marketing": False}
        
        for cookie in ["_ga", "_gid"]:
            assert middleware._is_cookie_allowed(cookie, consent) is False
    
    def test_analytics_cookies_allowed_with_consent(self):
        """Test that analytics cookies are allowed with consent"""
        from backend.api.middleware.cookie_consent import CookieConsentMiddleware
        
        middleware = CookieConsentMiddleware(MagicMock())
        consent = {"essential": True, "analytics": True, "marketing": False}
        
        for cookie in ["_ga", "_gid"]:
            assert middleware._is_cookie_allowed(cookie, consent) is True
    
    def test_marketing_cookies_blocked_without_consent(self):
        """Test that marketing cookies are blocked without consent"""
        from backend.api.middleware.cookie_consent import CookieConsentMiddleware
        
        middleware = CookieConsentMiddleware(MagicMock())
        consent = {"essential": True, "analytics": False, "marketing": False}
        
        assert middleware._is_cookie_allowed("_fbp", consent) is False
        assert middleware._is_cookie_allowed("fr", consent) is False
    
    def test_marketing_cookies_allowed_with_consent(self):
        """Test that marketing cookies are allowed with consent"""
        from backend.api.middleware.cookie_consent import CookieConsentMiddleware
        
        middleware = CookieConsentMiddleware(MagicMock())
        consent = {"essential": True, "analytics": False, "marketing": True}
        
        assert middleware._is_cookie_allowed("_fbp", consent) is True
        assert middleware._is_cookie_allowed("fr", consent) is True


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_process_export_for_nonexistent_request(
        self,
        compliance_service: ComplianceService,
    ):
        """Test that processing non-existent export returns None"""
        result = compliance_service.process_data_export(uuid.uuid4())
        assert result is None
    
    def test_process_deletion_for_nonexistent_request(
        self,
        compliance_service: ComplianceService,
    ):
        """Test that processing non-existent deletion returns False"""
        result = compliance_service.process_data_deletion(uuid.uuid4())
        assert result is False
    
    def test_cancel_deletion_for_nonexistent_request(
        self,
        compliance_service: ComplianceService,
        test_user: User,
    ):
        """Test that cancelling non-existent deletion returns False"""
        result = compliance_service.cancel_deletion_request(uuid.uuid4(), test_user.id)
        assert result is False
    
    def test_collect_data_for_nonexistent_user(
        self,
        compliance_service: ComplianceService,
    ):
        """Test that collecting data for non-existent user raises error"""
        with pytest.raises(ValueError):
            compliance_service._collect_user_data(uuid.uuid4())
    
    def test_get_export_download_wrong_user(
        self,
        compliance_service: ComplianceService,
        test_user: User,
        db_session: Session,
    ):
        """Test that get_export_download returns None for wrong user"""
        # Create export for test_user
        export_request = compliance_service.request_data_export(
            user_id=test_user.id,
            format="json",
        )
        compliance_service.process_data_export(export_request.id)
        
        # Try to get download with different user ID
        wrong_user_id = uuid.uuid4()
        result = compliance_service.get_export_download(export_request.id, wrong_user_id)
        
        assert result is None
