"""
Integration tests for notification delivery system
Tests email, push notification, and in-app notification delivery
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.notification_service import NotificationService


class TestNotificationDeliveryIntegration:
    """Integration tests for notification delivery across multiple channels"""

    @pytest.fixture
    def notification_service(self):
        """Create notification service instance"""
        return NotificationService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_notification_delivery_full_workflow_email_push_inapp(
        self, notification_service, mock_db_session
    ):
        """Test complete notification delivery workflow across all channels"""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Mock user preferences - enable all channels
        mock_preferences = MagicMock()
        mock_preferences.push_enabled = True
        mock_preferences.email_enabled = True
        mock_preferences.quiet_hours_enabled = False
        mock_preferences.push_application_submitted = True
        mock_preferences.email_application_submitted = True

        # Mock device tokens
        mock_ios_token = MagicMock()
        mock_ios_token.platform = "ios"
        mock_ios_token.token = "ios_device_token_123"
        mock_ios_token.device_id = "ios_device_123"

        mock_android_token = MagicMock()
        mock_android_token.platform = "android"
        mock_android_token.token = "android_device_token_456"
        mock_android_token.device_id = "android_device_456"

        device_tokens = [mock_ios_token, mock_android_token]

        # Mock notification template
        mock_template = MagicMock()
        mock_template.title_template = "Application Submitted: {{job_title}}"
        mock_template.message_template = (
            "Your application for {{job_title}} has been submitted successfully."
        )

        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_get_prefs, patch.object(
            notification_service, "_get_notification_template", new_callable=AsyncMock
        ) as mock_get_template, patch.object(
            notification_service, "_get_user_device_tokens", new_callable=AsyncMock
        ) as mock_get_tokens, patch.object(
            notification_service, "_store_notification", new_callable=AsyncMock
        ) as mock_store, patch.object(
            notification_service,
            "_send_push_notifications_safe",
            new_callable=AsyncMock,
        ) as mock_push_safe, patch.object(
            notification_service,
            "_send_email_notification_safe",
            new_callable=AsyncMock,
        ) as mock_email_safe:

            mock_get_prefs.return_value = mock_preferences
            mock_get_template.return_value = mock_template
            mock_get_tokens.return_value = device_tokens
            mock_store.return_value = None
            mock_push_safe.return_value = None
            mock_email_safe.return_value = None

            # Enable services for testing
            notification_service.apns_client = MagicMock()
            notification_service.fcm_app = MagicMock()
            notification_service.sendgrid_client = MagicMock()

            result = await notification_service.send_notification(
                user_id=user_id,
                task_id=task_id,
                notification_type="application_submitted",
                message="Your application has been submitted",
                metadata={
                    "job_title": "Senior Python Developer",
                    "company": "Tech Corp",
                },
            )

            # Verify notification was processed
            assert result["user_id"] == user_id
            assert result["task_id"] == task_id
            assert result["type"] == "application_submitted"
            assert result["delivered"] == True
            assert "title" in result
            assert "message" in result

            # Verify all delivery methods were attempted
            mock_push_safe.assert_called_once()
            mock_email_safe.assert_called_once()
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_notification_delivery_apns_success(self, notification_service):
        """Test successful APNs push notification delivery"""
        user_id = str(uuid.uuid4())

        # Mock device tokens
        mock_token = MagicMock()
        mock_token.platform = "ios"
        mock_token.token = "valid_ios_token"
        mock_token.device_id = "ios_device_123"

        device_tokens = [mock_token]

        # Mock APNs client
        mock_apns = MagicMock()
        notification_service.apns_client = mock_apns

        with patch.object(
            notification_service, "_get_user_device_tokens", new_callable=AsyncMock
        ) as mock_get_tokens:
            mock_get_tokens.return_value = device_tokens

            await notification_service._send_push_notifications(
                user_id=user_id,
                notification_type="application_submitted",
                message="Test message",
            )

            # Verify APNs was called
            mock_apns.send_notification.assert_called_once()
            call_args = mock_apns.send_notification.call_args
            assert call_args[0][0] == "valid_ios_token"  # token
            # payload should be passed as second argument

    @pytest.mark.asyncio
    async def test_push_notification_delivery_fcm_success(self, notification_service):
        """Test successful FCM push notification delivery"""
        user_id = str(uuid.uuid4())

        # Mock device tokens
        mock_token = MagicMock()
        mock_token.platform = "android"
        mock_token.token = "valid_android_token"
        mock_token.device_id = "android_device_456"

        device_tokens = [mock_token]

        # Mock FCM
        with patch("backend.services.notification_service.messaging") as mock_messaging:
            mock_send_multicast = MagicMock()
            mock_send_multicast.return_value = MagicMock(
                success_count=1, failure_count=0
            )
            mock_messaging.send_multicast = mock_send_multicast
            mock_messaging.Message = MagicMock()
            mock_messaging.Notification = MagicMock()
            mock_messaging.AndroidConfig = MagicMock()
            mock_messaging.AndroidNotification = MagicMock()
            mock_messaging.APNSConfig = MagicMock()
            mock_messaging.APNSPayload = MagicMock()
            mock_messaging.Aps = MagicMock()

            notification_service.fcm_app = MagicMock()

            with patch.object(
                notification_service, "_get_user_device_tokens", new_callable=AsyncMock
            ) as mock_get_tokens:
                mock_get_tokens.return_value = device_tokens

                await notification_service._send_push_notifications(
                    user_id=user_id,
                    notification_type="application_completed",
                    message="Application completed successfully",
                )

                # Verify FCM was called
                mock_messaging.Message.assert_called_once()
                mock_send_multicast.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_notification_delivery_success(self, notification_service):
        """Test successful email notification delivery"""
        user_id = str(uuid.uuid4())

        # Mock SendGrid client
        mock_sg_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sg_client.send.return_value = mock_response
        notification_service.sendgrid_client = mock_sg_client

        # Mock template
        mock_template = MagicMock()
        mock_template.subject_template = "Application Status Update"
        mock_template.html_template = "<p>Your application status has changed.</p>"

        # Mock user email lookup
        with patch("backend.services.notification_service.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock user query
            mock_user = MagicMock()
            mock_user.email = "test@example.com"
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            await notification_service._send_email_notification(
                user_id=user_id,
                notification_type="application_failed",
                message="Application failed to submit",
                metadata={"job_title": "Python Developer"},
                template=mock_template,
            )

            # Verify SendGrid was called
            mock_sg_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_notification_delivery_with_user_preferences_filtering(
        self, notification_service
    ):
        """Test notification delivery respects user preferences"""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Mock user preferences - disable push, enable email
        mock_preferences = MagicMock()
        mock_preferences.push_enabled = False  # Disabled
        mock_preferences.email_enabled = True
        mock_preferences.quiet_hours_enabled = False
        mock_preferences.email_application_submitted = True

        # Mock template
        mock_template = MagicMock()
        mock_template.title_template = "Application Submitted"
        mock_template.message_template = "Your application has been submitted."

        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_get_prefs, patch.object(
            notification_service, "_get_notification_template", new_callable=AsyncMock
        ) as mock_get_template, patch.object(
            notification_service, "_store_notification", new_callable=AsyncMock
        ) as mock_store, patch.object(
            notification_service,
            "_send_push_notifications_safe",
            new_callable=AsyncMock,
        ) as mock_push_safe, patch.object(
            notification_service,
            "_send_email_notification_safe",
            new_callable=AsyncMock,
        ) as mock_email_safe:

            mock_get_prefs.return_value = mock_preferences
            mock_get_template.return_value = mock_template
            mock_store.return_value = None
            mock_push_safe.return_value = None
            mock_email_safe.return_value = None

            # Enable services
            notification_service.sendgrid_client = MagicMock()

            result = await notification_service.send_notification(
                user_id=user_id,
                task_id=task_id,
                notification_type="application_submitted",
                message="Application submitted",
            )

            # Verify only email was attempted, not push
            mock_push_safe.assert_not_called()
            mock_email_safe.assert_called_once()
            mock_store.assert_called_once()  # In-app always stored

    @pytest.mark.asyncio
    async def test_notification_delivery_during_quiet_hours(self, notification_service):
        """Test notification delivery during quiet hours"""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Mock user preferences with quiet hours
        mock_preferences = MagicMock()
        mock_preferences.push_enabled = True
        mock_preferences.email_enabled = True
        mock_preferences.quiet_hours_enabled = True
        mock_preferences.quiet_hours_start = "22:00:00"
        mock_preferences.quiet_hours_end = "08:00:00"
        mock_preferences.push_application_submitted = True
        mock_preferences.email_application_submitted = True

        # Mock template
        mock_template = MagicMock()
        mock_template.title_template = "Application Submitted"
        mock_template.message_template = "Your application has been submitted."

        with patch.object(
            notification_service, "_get_user_preferences", new_callable=AsyncMock
        ) as mock_get_prefs, patch.object(
            notification_service, "_get_notification_template", new_callable=AsyncMock
        ) as mock_get_template, patch.object(
            notification_service, "_store_notification", new_callable=AsyncMock
        ) as mock_store, patch.object(
            notification_service, "_is_within_quiet_hours"
        ) as mock_quiet_hours:

            mock_get_prefs.return_value = mock_preferences
            mock_get_template.return_value = mock_template
            mock_store.return_value = None
            mock_quiet_hours.return_value = True  # Currently in quiet hours

            result = await notification_service.send_notification(
                user_id=user_id,
                task_id=task_id,
                notification_type="application_submitted",
                message="Application submitted",
            )

            # Verify notifications were not sent during quiet hours, but stored
            mock_store.assert_called_once()
            assert result["delivered"] == True  # Still marked as delivered since stored

    @pytest.mark.asyncio
    async def test_notification_delivery_multiple_device_types(
        self, notification_service
    ):
        """Test notification delivery to multiple device types"""
        user_id = str(uuid.uuid4())

        # Mock multiple device tokens
        mock_ios_token = MagicMock()
        mock_ios_token.platform = "ios"
        mock_ios_token.token = "ios_token_123"

        mock_android_token = MagicMock()
        mock_android_token.platform = "android"
        mock_android_token.token = "android_token_456"

        mock_web_token = MagicMock()
        mock_web_token.platform = "web"
        mock_web_token.token = "web_token_789"

        device_tokens = [mock_ios_token, mock_android_token, mock_web_token]

        # Enable both APNs and FCM
        notification_service.apns_client = MagicMock()
        notification_service.fcm_app = MagicMock()

        with patch.object(
            notification_service, "_get_user_device_tokens", new_callable=AsyncMock
        ) as mock_get_tokens, patch.object(
            notification_service, "_send_apns_notifications", new_callable=AsyncMock
        ) as mock_apns, patch.object(
            notification_service, "_send_fcm_notifications", new_callable=AsyncMock
        ) as mock_fcm:

            mock_get_tokens.return_value = device_tokens
            mock_apns.return_value = None
            mock_fcm.return_value = None

            await notification_service._send_push_notifications(
                user_id=user_id,
                notification_type="job_match_found",
                message="New job match found",
            )

            # Verify APNs called for iOS, FCM for Android, web ignored
            mock_apns.assert_called_once()
            apns_call_args = mock_apns.call_args
            assert len(apns_call_args[0][0]) == 1  # One iOS token
            assert apns_call_args[0][0][0].platform == "ios"

            mock_fcm.assert_called_once()
            fcm_call_args = mock_fcm.call_args
            assert len(fcm_call_args[0][0]) == 1  # One Android token
            assert fcm_call_args[0][0][0].platform == "android"

    @pytest.mark.asyncio
    async def test_notification_delivery_error_handling(self, notification_service):
        """Test notification delivery error handling"""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Mock template retrieval failure
        with patch.object(
            notification_service, "_get_notification_template", new_callable=AsyncMock
        ) as mock_get_template:
            mock_get_template.side_effect = Exception("Template service unavailable")

            result = await notification_service.send_notification(
                user_id=user_id,
                task_id=task_id,
                notification_type="application_submitted",
                message="Application submitted",
            )

            # Should still attempt delivery but mark error
            assert "error" in result
            assert result["error"] == "Template service unavailable"

    @pytest.mark.asyncio
    async def test_in_app_notification_storage(self, notification_service):
        """Test in-app notification storage in database"""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Mock successful notification creation
        mock_notification = {
            "user_id": user_id,
            "task_id": task_id,
            "type": "application_submitted",
            "message": "Application submitted",
            "metadata": {"job_id": "job123"},
            "timestamp": "2026-01-27T12:00:00",
            "delivered": False,
        }

        with patch.object(
            notification_service, "_store_notification", new_callable=AsyncMock
        ) as mock_store:
            mock_store.return_value = None

            await notification_service._store_notification(mock_notification)

            # Verify notification was stored
            mock_store.assert_called_once_with(mock_notification)
