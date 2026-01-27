"""
Integration tests for notification delivery.

Tests cover:
- Notification creation and storage
- Push notification delivery (mocked)
- Email notification delivery (mocked)
- User preference handling
- Quiet hours logic
- Template rendering
- Error handling and retries
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import models and services
from backend.db.models import (DeviceToken, Notification, NotificationTemplate,
                               User, UserNotificationPreferences)
from backend.services.notification_service import NotificationService
# Import test fixtures
from backend.tests.conftest import *


class TestNotificationService:
    """Test cases for NotificationService"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        session = MagicMock()
        return session

    @pytest.fixture
    def notification_service(self):
        """Create a NotificationService instance with mocked external services"""
        with patch("backend.services.notification_service.aioapns", None):
            with patch("backend.services.notification_service.messaging", None):
                with patch("backend.services.notification_service.sendgrid", None):
                    service = NotificationService()
                    return service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing"""
        user = MagicMock(spec=User)
        user.id = "test-user-123"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def sample_preferences(self):
        """Create sample notification preferences"""
        prefs = MagicMock(spec=UserNotificationPreferences)
        prefs.push_enabled = True
        prefs.email_enabled = True
        prefs.quiet_hours_enabled = False
        prefs.quiet_hours_start = "22:00"
        prefs.quiet_hours_end = "08:00"
        prefs.push_application_submitted = True
        prefs.push_application_completed = True
        prefs.push_application_failed = True
        prefs.push_captcha_detected = True
        prefs.push_job_match_found = True
        prefs.push_system_notification = True
        prefs.email_application_submitted = False
        prefs.email_application_completed = True
        prefs.email_application_failed = True
        prefs.email_captcha_detected = True
        prefs.email_job_match_found = True
        prefs.email_system_notification = True
        return prefs

    @pytest.fixture
    def sample_device_token(self):
        """Create a sample device token"""
        token = MagicMock(spec=DeviceToken)
        token.token = "test-device-token-123"
        token.platform = "ios"
        return token

    @pytest.fixture
    def sample_template(self):
        """Create a sample notification template"""
        template = MagicMock(spec=NotificationTemplate)
        template.title_template = "Application {{action}}"
        template.message_template = (
            "Your application for {{job_title}} has been {{action}}"
        )
        template.email_html_template = None
        template.channels = ["push", "email"]
        return template

    # ============================================================
    # Test: Service Initialization
    # ============================================================

    def test_service_initialization(self, notification_service):
        """Test that service initializes correctly without external services"""
        assert notification_service.apns_enabled is False
        assert notification_service.fcm_enabled is False
        assert notification_service.email_enabled is False

    # ============================================================
    # Test: Quiet Hours Logic
    # ============================================================

    def test_not_within_quiet_hours_disabled(
        self, notification_service, sample_preferences
    ):
        """Test quiet hours when disabled"""
        sample_preferences.quiet_hours_enabled = False
        result = notification_service._is_within_quiet_hours(sample_preferences)
        assert result is False

    def test_not_within_quiet_hours_no_preferences(self, notification_service):
        """Test quiet hours when no preferences exist"""
        result = notification_service._is_within_quiet_hours(None)
        assert result is False

    @pytest.mark.parametrize(
        "current_time,start,end,expected",
        [
            ("10:00:00", "22:00", "08:00", False),  # Morning, outside quiet hours
            ("23:00:00", "22:00", "08:00", True),  # Night, within quiet hours
            ("07:00:00", "22:00", "08:00", True),  # Early morning, within quiet hours
            ("12:00:00", "09:00", "17:00", False),  # Midday, outside standard hours
        ],
    )
    def test_quiet_hours_various_times(
        self,
        notification_service,
        sample_preferences,
        current_time,
        start,
        end,
        expected,
    ):
        """Test quiet hours logic for various times"""
        sample_preferences.quiet_hours_enabled = True
        sample_preferences.quiet_hours_start = start
        sample_preferences.quiet_hours_end = end

        with patch("backend.services.notification_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.strptime(current_time, "%H:%M:%S")
            mock_datetime.now.time.return_value = datetime.strptime(
                current_time, "%H:%M:%S"
            ).time()

            result = notification_service._is_within_quiet_hours(sample_preferences)
            assert result == expected

    # ============================================================
    # Test: Push Notification Decision
    # ============================================================

    def test_should_send_push_notification_disabled(
        self, notification_service, sample_preferences
    ):
        """Test push notification decision when disabled"""
        sample_preferences.push_enabled = False
        result = notification_service._should_send_push_notification(
            "application_submitted", sample_preferences
        )
        assert result is False

    def test_should_send_push_notification_enabled_for_type(
        self, notification_service, sample_preferences
    ):
        """Test push notification decision when enabled for specific type"""
        result = notification_service._should_send_push_notification(
            "application_submitted", sample_preferences
        )
        assert result is True

    def test_should_send_push_notification_disabled_for_type(
        self, notification_service, sample_preferences
    ):
        """Test push notification decision when disabled for specific type"""
        sample_preferences.push_application_submitted = False
        result = notification_service._should_send_push_notification(
            "application_submitted", sample_preferences
        )
        assert result is False

    def test_should_send_push_notification_no_preferences(self, notification_service):
        """Test push notification decision when no preferences"""
        result = notification_service._should_send_push_notification(
            "application_submitted", None
        )
        assert result is False

    # ============================================================
    # Test: Email Notification Decision
    # ============================================================

    def test_should_send_email_notification_disabled(
        self, notification_service, sample_preferences
    ):
        """Test email notification decision when disabled"""
        sample_preferences.email_enabled = False
        result = notification_service._should_send_email_notification(
            "application_submitted", sample_preferences
        )
        assert result is False

    def test_should_send_email_notification_enabled_for_type(
        self, notification_service, sample_preferences
    ):
        """Test email notification decision when enabled for specific type"""
        result = notification_service._should_send_email_notification(
            "application_completed", sample_preferences
        )
        assert result is True

    def test_should_send_email_notification_disabled_for_type(
        self, notification_service, sample_preferences
    ):
        """Test email notification decision when disabled for specific type"""
        sample_preferences.email_application_submitted = False
        result = notification_service._should_send_email_notification(
            "application_submitted", sample_preferences
        )
        assert result is False

    def test_should_send_email_notification_no_preferences(self, notification_service):
        """Test email notification decision when no preferences"""
        result = notification_service._should_send_email_notification(
            "application_submitted", None
        )
        assert result is False

    # ============================================================
    # Test: Notification Title Generation
    # ============================================================

    @pytest.mark.parametrize(
        "notification_type,expected_title",
        [
            ("application_submitted", "Application Submitted"),
            ("application_completed", "Application Completed"),
            ("application_failed", "Application Failed"),
            ("captcha_detected", "Action Required"),
            ("job_match_found", "New Job Match"),
            ("profile_updated", "Profile Updated"),
            ("system_notification", "System Notification"),
            ("unknown_type", "Notification"),
        ],
    )
    def test_get_notification_title(
        self, notification_service, notification_type, expected_title
    ):
        """Test notification title generation for various types"""
        result = notification_service._get_notification_title(notification_type)
        assert result == expected_title

    # ============================================================
    # Test: Template Rendering
    # ============================================================

    def test_render_template_simple(self, notification_service):
        """Test simple template rendering"""
        template = "Hello {{name}}, your job {{action}} is complete."
        variables = {"name": "John", "action": "application"}
        result = notification_service._render_template(template, variables)
        assert result == "Hello John, your job application is complete."

    def test_render_template_no_variables(self, notification_service):
        """Test template rendering with no variables"""
        template = "Simple notification message"
        variables = {}
        result = notification_service._render_template(template, variables)
        assert result == "Simple notification message"

    def test_render_template_missing_variable(self, notification_service):
        """Test template rendering with missing variable (keeps placeholder)"""
        template = "Hello {{name}}, welcome to {{platform}}"
        variables = {"name": "John"}  # platform is missing
        result = notification_service._render_template(template, variables)
        assert result == "Hello John, welcome to {{platform}}"

    # ============================================================
    # Test: Notification Validation
    # ============================================================

    def test_validate_notification_data_valid(self, notification_service):
        """Test validation with valid data"""
        result = notification_service._validate_notification_data(
            "user-123", "application_submitted", "Test message"
        )
        assert result is True

    def test_validate_notification_data_empty_user_id(self, notification_service):
        """Test validation with empty user ID"""
        result = notification_service._validate_notification_data(
            "", "application_submitted", "Test message"
        )
        assert result is False

    def test_validate_notification_data_empty_type(self, notification_service):
        """Test validation with empty notification type"""
        result = notification_service._validate_notification_data(
            "user-123", "", "Test message"
        )
        assert result is False

    def test_validate_notification_data_empty_message(self, notification_service):
        """Test validation with empty message"""
        result = notification_service._validate_notification_data(
            "user-123", "application_submitted", ""
        )
        assert result is False

    def test_validate_notification_data_none_values(self, notification_service):
        """Test validation with None values"""
        result = notification_service._validate_notification_data(None, None, None)
        assert result is False

    # ============================================================
    # Test: Mock Push Notification Sending
    # ============================================================

    @pytest.mark.asyncio
    async def test_send_push_notification_mock(
        self, notification_service, sample_device_token
    ):
        """Test push notification sending with mocked APNs/FCM"""
        with patch.object(notification_service, "apns_client", None):
            with patch.object(notification_service, "fcm_app", None):
                # Should not raise, just log warning
                await notification_service._send_push_notifications_safe(
                    "user-123", "application_submitted", "Test message", {}
                )

    @pytest.mark.asyncio
    async def test_send_push_notification_success_mock(
        self, notification_service, sample_device_token
    ):
        """Test successful push notification sending with mocked client"""
        # Create mock APNs client
        mock_apns = AsyncMock()
        mock_apns.send_notification.return_value = True

        with patch.object(notification_service, "apns_client", mock_apns):
            with patch.object(notification_service, "fcm_app", None):
                # Should complete without error
                await notification_service._send_push_notifications_safe(
                    "user-123", "application_submitted", "Test message", {}
                )

    # ============================================================
    # Test: Mock Email Notification Sending
    # ============================================================

    @pytest.mark.asyncio
    async def test_send_email_notification_mock(self, notification_service):
        """Test email notification sending with mocked SendGrid"""
        with patch.object(notification_service, "sendgrid_client", None):
            # Should not raise, just log warning
            await notification_service._send_email_notification_safe(
                "user-123", "application_submitted", "Test message", {}, None
            )

    @pytest.mark.asyncio
    async def test_send_email_notification_success_mock(self, notification_service):
        """Test successful email notification sending with mocked client"""
        mock_sendgrid = MagicMock()
        mock_sendgrid.send.return_value = True

        with patch.object(notification_service, "sendgrid_client", mock_sendgrid):
            await notification_service._send_email_notification_safe(
                "user-123",
                "application_completed",
                "Your application was completed",
                {},
                None,
            )

    # ============================================================
    # Test: Full Notification Flow (Integration Test)
    # ============================================================

    @pytest.mark.asyncio
    async def test_send_notification_complete_flow(
        self, notification_service, sample_preferences, sample_device_token
    ):
        """Test complete notification sending flow"""
        user_id = "test-user-123"
        task_id = "test-task-456"
        notification_type = "application_completed"
        message = "Your application has been completed successfully"
        metadata = {"job_title": "Software Engineer", "company": "Acme Inc"}

        # Mock dependencies
        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_prefs:
            mock_prefs.return_value = sample_preferences

            with patch.object(
                notification_service,
                "_get_notification_template",
                new_callable=AsyncMock,
            ) as mock_template:
                mock_template.return_value = None  # No template, use default

                with patch.object(
                    notification_service, "_store_notification", new_callable=AsyncMock
                ) as mock_store:
                    mock_store.return_value = None

                    # Execute
                    result = await notification_service.send_notification(
                        user_id=user_id,
                        task_id=task_id,
                        notification_type=notification_type,
                        message=message,
                        metadata=metadata,
                    )

                    # Verify
                    assert result["user_id"] == user_id
                    assert result["task_id"] == task_id
                    assert result["type"] == notification_type
                    assert result["delivered"] is True
                    assert "error" not in result

    @pytest.mark.asyncio
    async def test_send_notification_quiet_hours(
        self, notification_service, sample_preferences
    ):
        """Test notification respects quiet hours"""
        user_id = "test-user-123"
        task_id = "test-task-456"
        notification_type = "application_completed"
        message = "Your application has been completed"
        metadata = {"job_title": "Software Engineer"}

        # Enable quiet hours for current time
        sample_preferences.quiet_hours_enabled = True

        # Mock that we're within quiet hours
        current_time = time(23, 0, 0)  # 11 PM
        start_time = time(22, 0, 0)  # 10 PM
        end_time = time(8, 0, 0)  # 8 AM

        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_prefs:
            mock_prefs.return_value = sample_preferences

            with patch(
                "backend.services.notification_service.datetime"
            ) as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(
                    datetime.today(), current_time
                )

                with patch.object(
                    notification_service, "_store_notification", new_callable=AsyncMock
                ) as mock_store:
                    mock_store.return_value = None

                    result = await notification_service.send_notification(
                        user_id=user_id,
                        task_id=task_id,
                        notification_type=notification_type,
                        message=message,
                        metadata=metadata,
                    )

                    # Should still be delivered (stored in DB) even during quiet hours
                    assert result["delivered"] is True

    @pytest.mark.asyncio
    async def test_send_notification_preferences_disabled(self, notification_service):
        """Test notification when all preferences are disabled"""
        user_id = "test-user-123"
        task_id = "test-task-456"
        notification_type = "application_submitted"
        message = "Application submitted"
        metadata = {}

        # Create preferences with all notifications disabled
        sample_preferences.push_enabled = False
        sample_preferences.email_enabled = False

        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_prefs:
            mock_prefs.return_value = sample_preferences

            with patch.object(
                notification_service, "_store_notification", new_callable=AsyncMock
            ) as mock_store:
                mock_store.return_value = None

                result = await notification_service.send_notification(
                    user_id=user_id,
                    task_id=task_id,
                    notification_type=notification_type,
                    message=message,
                    metadata=metadata,
                )

                # Should still be stored in database
                assert result["delivered"] is True
                mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_invalid_data(self, notification_service):
        """Test notification handling with invalid data"""
        result = await notification_service.send_notification(
            user_id="",
            task_id="task-123",
            notification_type="application_submitted",
            message="Test",
            metadata={},
        )

        assert result["delivered"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_send_notification_exception_handling(
        self, notification_service, sample_preferences
    ):
        """Test notification handles exceptions gracefully"""
        user_id = "test-user-123"

        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_prefs:
            # Simulate database error
            mock_prefs.side_effect = Exception("Database connection failed")

            result = await notification_service.send_notification(
                user_id=user_id,
                task_id="task-123",
                notification_type="application_submitted",
                message="Test message",
                metadata={},
            )

            # Should handle error gracefully
            assert result["delivered"] is False
            assert "error" in result
            assert "Database connection failed" in result["error"]


class TestNotificationTemplates:
    """Test cases for notification template functionality"""

    @pytest.fixture
    def notification_service(self):
        """Create a NotificationService instance"""
        with patch("backend.services.notification_service.aioapns", None):
            with patch("backend.services.notification_service.messaging", None):
                with patch("backend.services.notification_service.sendgrid", None):
                    return NotificationService()

    def test_template_rendering_with_variables(self, notification_service):
        """Test template rendering with all variables present"""
        template = "{{greeting}} {{name}}, your application for {{job_title}} at {{company}} {{action}}"
        variables = {
            "greeting": "Hello",
            "name": "John",
            "job_title": "Software Engineer",
            "company": "Acme Inc",
            "action": "was submitted",
        }
        result = notification_service._render_template(template, variables)
        expected = "Hello John, your application for Software Engineer at Acme Inc was submitted"
        assert result == expected

    def test_template_rendering_special_characters(self, notification_service):
        """Test template rendering with special characters"""
        template = "Job: {{job_title}} - Location: {{location}}"
        variables = {
            "job_title": 'Software Engineer "Lead"',
            "location": "New York, NY",
        }
        result = notification_service._render_template(template, variables)
        assert "Software Engineer" in result
        assert "New York" in result

    def test_template_rendering_empty_variables(self, notification_service):
        """Test template rendering with empty variable values"""
        template = "Name: {{name}}, Age: {{age}}"
        variables = {"name": "John", "age": ""}
        result = notification_service._render_template(template, variables)
        assert result == "Name: John, Age: "


class TestNotificationPreferencesEdgeCases:
    """Test edge cases for notification preferences"""

    @pytest.fixture
    def notification_service(self):
        """Create a NotificationService instance"""
        with patch("backend.services.notification_service.aioapns", None):
            with patch("backend.services.notification_service.messaging", None):
                with patch("backend.services.notification_service.sendgrid", None):
                    return NotificationService()

    def test_quiet_hours_overnight_crossing(self, notification_service):
        """Test quiet hours when overnight (e.g., 23:00 to 07:00)"""
        prefs = MagicMock()
        prefs.quiet_hours_enabled = True
        prefs.quiet_hours_start = "23:00"
        prefs.quiet_hours_end = "07:00"

        with patch("backend.services.notification_service.datetime") as mock_datetime:
            # Test at 01:00 (should be within quiet hours)
            mock_datetime.now.return_value = datetime(2024, 1, 15, 1, 0, 0)
            mock_datetime.now.time.return_value = time(1, 0, 0)

            result = notification_service._is_within_quiet_hours(prefs)
            assert result is True

    def test_quiet_hours_invalid_time_format(self, notification_service):
        """Test quiet hours with invalid time format"""
        prefs = MagicMock()
        prefs.quiet_hours_enabled = True
        prefs.quiet_hours_start = "invalid"
        prefs.quiet_hours_end = "time"

        # Should not crash, should return False
        result = notification_service._is_within_quiet_hours(prefs)
        assert result is False

    def test_unknown_notification_type(self, notification_service, sample_preferences):
        """Test handling of unknown notification type"""
        # Unknown types should default to not sending
        result = notification_service._should_send_push_notification(
            "unknown_type_xyz", sample_preferences
        )
        assert result is False

        result = notification_service._should_send_email_notification(
            "unknown_type_xyz", sample_preferences
        )
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
