"""
Notification Service

Handles sending notifications to users via various channels.
"""

import asyncio
import logging
import os
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from db.database import get_db
from db.models import (DeviceToken, Notification, NotificationTemplate,
                               UserNotificationPreferences)

logger = logging.getLogger(__name__)

# Import notification libraries (will be available in production)
try:
    import aioapns
    import firebase_admin
    import sendgrid
    from firebase_admin import credentials, messaging
    from sendgrid.helpers.mail import Content, Email, Mail, To
except ImportError:
    logger.warning(
        "Notification libraries not available - push notifications and email will be disabled"
    )
    aioapns = None
    messaging = None
    credentials = None
    firebase_admin = None
    sendgrid = None
    Mail = None
    Email = None
    To = None
    Content = None


class NotificationService:
    """Service for sending user notifications"""

    def __init__(self):
        # Initialize notification services
        self.apns_client = None
        self.fcm_app = None
        self.sendgrid_client = None

        # Check environment variables and initialize services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize notification service clients"""

        # APNs (Apple Push Notification Service)
        apns_key_id = os.getenv("APNS_KEY_ID")
        apns_team_id = os.getenv("APNS_TEAM_ID")
        apns_auth_key_path = os.getenv("APNS_AUTH_KEY_PATH")

        if apns_key_id and apns_team_id and apns_auth_key_path and aioapns:
            try:
                self.apns_client = aioapns.APNs(
                    key_id=apns_key_id,
                    team_id=apns_team_id,
                    auth_key_path=apns_auth_key_path,
                    use_sandbox=os.getenv("APNS_SANDBOX", "false").lower() == "true",
                )
                logger.info("APNs client initialized")
            except Exception as e:
                logger.error("Failed to initialize APNs client: %s", e)

        # FCM (Firebase Cloud Messaging)
        fcm_credentials_path = os.getenv("FCM_CREDENTIALS_PATH")
        if fcm_credentials_path and firebase_admin and credentials:
            try:
                cred = credentials.Certificate(fcm_credentials_path)
                self.fcm_app = firebase_admin.initialize_app(cred)
                logger.info("FCM client initialized")
            except Exception as e:
                logger.error("Failed to initialize FCM client: %s", e)

        # SendGrid (Email service)
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_api_key and sendgrid:
            try:
                self.sendgrid_client = sendgrid.SendGridAPIClient(
                    api_key=sendgrid_api_key
                )
                logger.info("SendGrid client initialized")
            except Exception as e:
                logger.error("Failed to initialize SendGrid client: %s", e)

    @property
    def apns_enabled(self) -> bool:
        return self.apns_client is not None

    @property
    def fcm_enabled(self) -> bool:
        return self.fcm_app is not None

    @property
    def email_enabled(self) -> bool:
        return self.sendgrid_client is not None

    # Notification type to title mapping
    NOTIFICATION_TITLES = {
        "application_submitted": "Application Submitted",
        "application_completed": "Application Completed",
        "application_failed": "Application Failed",
        "captcha_detected": "Action Required",
        "job_match_found": "New Job Match",
        "profile_updated": "Profile Updated",
        "system_notification": "System Notification",
        "email_verification": "Email Verification",
        "password_reset": "Password Reset",
    }

    def _get_notification_title(self, notification_type: str) -> str:
        """Get human-readable title for notification type"""
        return self.NOTIFICATION_TITLES.get(notification_type, "Notification")

    async def send_notification(
        self,
        user_id: str,
        task_id: str,
        notification_type: str,
        message: str,
        metadata: Dict[str, Any] = None,
    ):
        """
        Send a notification to a user.

        Args:
            user_id: User ID to send notification to
            task_id: Related application task ID
            notification_type: Type of notification
            message: Notification message
            metadata: Additional metadata
        """
        notification = {
            "user_id": user_id,
            "task_id": task_id,
            "type": notification_type,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "delivered": False,
        }

        try:
            # Validate input data
            if not self._validate_notification_data(
                user_id, notification_type, message
            ):
                notification["error"] = "Invalid notification data"
                return notification

            # Get notification template
            template = await self._get_notification_template(notification_type)
            if not template:
                logger.warning("No template found for notification type: %s" % (notification_type)
                )
                # Fall back to basic notification without template
                rendered_title = self._get_notification_title(notification_type)
                rendered_message = message
            

            # Render template with metadata
            rendered_title = self._render_template(
                template.title_template, metadata
            )
            rendered_message = self._render_template(
                template.message_template, metadata
            )

            # Get user preferences
            preferences = await self._get_user_preferences(user_id)

            # Check if notification should be sent during quiet hours
            if not self._is_within_quiet_hours(preferences):
                # Send push notifications with retry logic
                if self._should_send_push_notification(notification_type, preferences):
                    await self._send_push_notifications_safe(
                        user_id, notification_type, rendered_message, metadata
                    )

                # Send email notifications with retry logic
                if self._should_send_email_notification(notification_type, preferences):
                    await self._send_email_notification_safe(
                        user_id, notification_type, rendered_message, metadata, template
                    )

            # Store in database for app to fetch (always store)
            notification["title"] = rendered_title
            notification["message"] = rendered_message
            await self._store_notification(notification)

            notification["delivered"] = True
            logger.info("Notification sent to user %s: %s", ('user_id', 'notification_type'))

        except Exception as e:
            logger.error("Failed to send notification: %s", e)
            notification["error"] = str(e)

        return notification

    async def _get_user_preferences(
        self, user_id: str
    ) -> Optional[UserNotificationPreferences]:
        """Get user notification preferences"""
        db = next(get_db())
        try:
            preferences = (
                db.query(UserNotificationPreferences)
                .filter(UserNotificationPreferences.user_id == user_id)
                .first()
            )
            return preferences
        except Exception as e:
            logger.error("Failed to get user preferences: %s", e)
            return None
        finally:
            db.close()

    def _is_within_quiet_hours(
        self, preferences: Optional[UserNotificationPreferences]
    ) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences or not preferences.quiet_hours_enabled:
            return False

        try:
            now = datetime.now().time()
            start_time = time.fromisoformat(preferences.quiet_hours_start)
            end_time = time.fromisoformat(preferences.quiet_hours_end)

            if start_time <= end_time:
                # Same day range
                return start_time <= now <= end_time
            

            # Overnight range
                return now >= start_time or now <= end_time
        except Exception as e:
            logger.error("Error checking quiet hours: %s", e)
            return False

    def _should_send_push_notification(
        self, notification_type: str, preferences: Optional[UserNotificationPreferences]
    ) -> bool:
        """Check if push notification should be sent"""
        if not preferences or not preferences.push_enabled:
            return False

        # Map notification types to preference fields
        type_mapping = {
            "application_submitted": preferences.push_application_submitted,
            "application_completed": preferences.push_application_completed,
            "application_failed": preferences.push_application_failed,
            "captcha_detected": preferences.push_captcha_detected,
            "job_match_found": preferences.push_job_match_found,
            "system_notification": preferences.push_system_notification,
        }

        return type_mapping.get(notification_type, False)

    def _should_send_email_notification(
        self, notification_type: str, preferences: Optional[UserNotificationPreferences]
    ) -> bool:
        """Check if email notification should be sent"""
        if not preferences or not preferences.email_enabled:
            return False

        # Map notification types to preference fields
        type_mapping = {
            "application_submitted": preferences.email_application_submitted,
            "application_completed": preferences.email_application_completed,
            "application_failed": preferences.email_application_failed,
            "captcha_detected": preferences.email_captcha_detected,
            "job_match_found": preferences.email_job_match_found,
            "system_notification": preferences.email_system_notification,
            "email_verification": True,  # Always send verification emails if email is enabled
            "password_reset": True,  # Always send password reset emails if email is enabled
        }

        return type_mapping.get(notification_type, False)

    async def _send_push_notifications(
        self, user_id: str, notification_type: str, message: str, metadata: Dict = None
    ):
        """Send push notifications to user's devices"""
        try:
            # Get user's device tokens
            device_tokens = await self._get_user_device_tokens(user_id)

            title = self._get_notification_title(notification_type)

            # Send to iOS devices via APNs
            ios_tokens = [token for token in device_tokens if token.platform == "ios"]
            if ios_tokens and self.apns_enabled:
                await self._send_apns_notifications(
                    ios_tokens, title, message, metadata
                )

            # Send to Android devices via FCM
            android_tokens = [
                token for token in device_tokens if token.platform == "android"
            ]
            if android_tokens and self.fcm_enabled:
                await self._send_fcm_notifications(
                    android_tokens, title, message, metadata
                )

        except Exception as e:
            logger.error("Failed to send push notifications: %s", e)

    async def _get_user_device_tokens(self, user_id: str) -> List[DeviceToken]:
        """Get user's device tokens"""
        db = next(get_db())
        try:
            tokens = db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()
            return tokens
        except Exception as e:
            logger.error("Failed to get device tokens: %s", e)
            return []
        finally:
            db.close()

    async def _send_apns_notifications(
        self,
        device_tokens: List[DeviceToken],
        title: str,
        message: str,
        metadata: Dict = None,
    ):
        """Send push notifications via APNs to multiple iOS devices"""
        if not self.apns_client:
            return

        try:
            for token in device_tokens:
                try:
                    # Create APNs payload
                    payload = aioapns.NotificationPayload(
                        alert=aioapns.Alert(title=title, body=message),
                        badge=1,
                        sound="default",
                        custom_data=metadata or {},
                    )

                    # Send notification
                    await self.apns_client.send_notification(token.token, payload)
                    logger.debug("APNs notification sent to device %s", token.device_id)

                except Exception as e:
                    logger.error("Failed to send APNs notification to device %s: %s" % (token.device_id, e)
                    )

        except Exception as e:
            logger.error("Failed to send APNs notifications: %s", e)

    async def _send_fcm_notifications(
        self,
        device_tokens: List[DeviceToken],
        title: str,
        message: str,
        metadata: Dict = None,
    ):
        """Send push notifications via FCM to multiple Android devices"""
        if not self.fcm_app or not messaging:
            return

        try:
            # Create FCM message
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data={
                    k: str(v) for k, v in (metadata or {}).items()
                },  # FCM data must be strings
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        priority="high",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                        ),
                    ),
                ),
            )

            # Send to multiple tokens
            tokens = [token.token for token in device_tokens]
            response = messaging.send_multicast(fcm_message, tokens)

            logger.debug("FCM notifications sent: %s successful, %s failed" % (response.success_count, response.failure_count)
            )

            # Handle failures (token cleanup, etc.)
            if response.failure_count > 0:
                for i, result in enumerate(response.responses):
                    if not result.success:
                        token = device_tokens[i]
                        logger.warning("FCM notification failed for device %s: %s" % (token.device_id, result.exception)
                        )

        except Exception as e:
            logger.error("Failed to send FCM notifications: %s", e)

    async def send_email_verification(self, user_id: str, verification_token: str):
        """Send email verification notification to user
        
        Args:
            user_id: User ID to send verification email to
            verification_token: Verification token to include in the email
        """
        metadata = {"verification_token": verification_token}
        message = "Please verify your email address to complete your registration"
        
        await self.send_notification(
            user_id=user_id,
            task_id=None,
            notification_type="email_verification",
            message=message,
            metadata=metadata
        )

    async def send_password_reset(self, user_id: str, reset_token: str):
        """Send password reset notification to user
        
        Args:
            user_id: User ID to send reset email to
            reset_token: Reset token to include in the email
        """
        metadata = {"reset_token": reset_token}
        message = "You requested a password reset. Please click the link below to reset your password"
        
        await self.send_notification(
            user_id=user_id,
            task_id=None,
            notification_type="password_reset",
            message=message,
            metadata=metadata
        )

    async def _send_email_notification(
        self,
        user_id: str,
        notification_type: str,
        message: str,
        metadata: Dict = None,
        template: NotificationTemplate = None,
    ):
        """Send email notification via SendGrid"""
        if not self.sendgrid_client or not sendgrid:
            return

        try:
            # Get user email
            user_email = await self._get_user_email(user_id)
            if not user_email:
                logger.warning("No email found for user %s", user_id)
                return

            # Use template HTML if available, otherwise fallback to basic template
            if template and template.email_html_template:
                subject = self._render_template(template.title_template, metadata)
                html_content = self._render_template(
                    template.email_html_template, metadata
                )
            

            subject, html_content = self._get_email_template(
                notification_type, message, metadata
            )

            # Create email
            from_email = Email(os.getenv("FROM_EMAIL", "noreply@jobswipe.com"))
            to_email = To(user_email)
            content = Content("text/html", html_content)
            mail = Mail(from_email, to_email, subject, content)

            # Send email
            response = self.sendgrid_client.send(mail)

            if response.status_code == 202:
                logger.debug("Email notification sent to user %s", user_id)
            else:
                logger.error("Failed to send email to user %s: %s - %s" % (user_id, response.status_code, response.body)
                )

        except Exception as e:
            logger.error("Failed to send email notification: %s", e)

    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user's email address"""
        db = next(get_db())
        try:
            from db.models import User

            user = db.query(User).filter(User.id == user_id).first()
            return user.email if user else None
        except Exception as e:
            logger.error("Failed to get user email: %s", e)
            return None
        finally:
            db.close()

    def _get_email_template(
        self, notification_type: str, message: str, metadata: Dict = None
    ) -> tuple[str, str]:
        """Get email template for notification type"""
        title = self._get_notification_title(notification_type)
        metadata = metadata or {}

        # Specific templates for verification and password reset
        if notification_type == "email_verification":
            verification_token = metadata.get("verification_token", "")
            from config import settings
            verification_url = settings.frontend_url + f"/verify-email?token={verification_token}"
            
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
                    .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                    .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .button:hover {{ background-color: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>{title}</h2>
                    </div>
                    <div class="content">
                        <p>{message}</p>
                        <p>Please click the button below to verify your email address:</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email</a>
                        </p>
                        <p>If you didn't request this verification, please ignore this email.</p>
                        <p>Alternatively, you can copy and paste this URL into your browser:</p>
                        <p style="font-family: monospace; background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">
                            {verification_url}
                        </p>
            """
        elif notification_type == "password_reset":
            reset_token = metadata.get("reset_token", "")
            from config import settings
            reset_url = settings.frontend_url + f"/reset-password?token={reset_token}"
            
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
                    .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                    .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .button:hover {{ background-color: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>{title}</h2>
                    </div>
                    <div class="content">
                        <p>{message}</p>
                        <p>Please click the button below to reset your password:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>This link will expire in 1 hour. If you didn't request this password reset, please ignore this email.</p>
                        <p>Alternatively, you can copy and paste this URL into your browser:</p>
                        <p style="font-family: monospace; background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">
                            {reset_url}
                        </p>
            """
        else:
            # Default template for other notification types
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
                    .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobSwipe</h1>
                        <h2>{title}</h2>
                    </div>
                    <div class="content">
                        <p>{message}</p>
                        {"".join(f"<p><strong>{k}:</strong> {v}</p>" for k, v in metadata.items())}
                </div>
                <div class="footer">
                    <p>You received this notification because you have notifications enabled for {notification_type.replace('_', ' ')}.</p>
                    <p>You can manage your notification preferences in the app.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return title, html_template

    async def _store_notification(self, notification: Dict):
        """Store notification in database for app to fetch"""
        db = next(get_db())
        try:
            db_notification = Notification(
                user_id=notification["user_id"],
                task_id=notification.get("task_id"),
                type=notification["type"],
                title=self._get_notification_title(notification["type"]),
                message=notification["message"],
                metadata=notification.get("metadata", {}),
                delivered=notification.get("delivered", False),
            )
            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)
            logger.debug("Notification stored: %s", db_notification.id)
        except Exception as e:
            db.rollback()
            logger.error("Failed to store notification: %s", e)
            raise
        finally:
            db.close()

    async def get_user_notifications(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            limit: Maximum number of notifications to return

        Returns:
            List of user notifications
        """
        db = next(get_db())
        try:
            notifications = (
                db.query(Notification)
                .filter(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "metadata": n.metadata,
                    "read": n.read,
                    "delivered": n.delivered,
                    "created_at": n.created_at.isoformat(),
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                }
                for n in notifications
            ]
        except Exception as e:
            logger.error("Failed to get user notifications: %s", e)
            return []
        finally:
            db.close()

    async def mark_notification_read(self, user_id: str, notification_id: str):
        """
        Mark a notification as read.

        Args:
            user_id: User ID
            notification_id: Notification ID
        """
        from uuid import UUID

        db = next(get_db())
        try:
            notification = (
                db.query(Notification)
                .filter(
                    Notification.id == UUID(notification_id),
                    Notification.user_id == UUID(user_id),
                )
                .first()
            )

            if notification:
                notification.read = True
                notification.read_at = datetime.now()
                db.commit()
                logger.debug("Marked notification %s as read for user %s" % (notification_id, user_id)
                )
            

            logger.warning("Notification %s not found for user %s" % (notification_id, user_id)
            )
        except Exception as e:
            db.rollback()
            logger.error("Failed to mark notification as read: %s", e)
        finally:
            db.close()

    async def _get_notification_template(
        self, notification_type: str
    ) -> Optional[NotificationTemplate]:
        """Get notification template by type"""
        db = next(get_db())
        try:
            template = (
                db.query(NotificationTemplate)
                .filter(
                    NotificationTemplate.name == notification_type,
                    NotificationTemplate.is_active is True,
                )
                .first()
            )
            return template
        except Exception as e:
            logger.error("Failed to get notification template: %s", e)
            return None
        finally:
            db.close()

    def _render_template(self, template: str, context: Dict = None) -> str:
        """Render template with context variables"""
        if not template or not context:
            return template or ""

        try:
            # Simple template rendering using string formatting
            result = template
            for key, value in (context or {}).items():
                placeholder = "{{" + key + "}}"
                result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.error("Failed to render template: %s", e)
            return template

    async def register_device_token(
        self,
        user_id: str,
        device_id: str,
        platform: str,
        token: str,
        app_version: str = None,
    ) -> bool:
        """
        Register or update a device token for push notifications.

        Args:
            user_id: User ID
            device_id: Unique device identifier
            platform: 'ios' or 'android'
            token: Push notification token
            app_version: App version (optional)

        Returns:
            Success status
        """
        db = next(get_db())
        try:
            # Check if token already exists
            existing_token = (
                db.query(DeviceToken).filter(DeviceToken.token == token).first()
            )

            if existing_token:
                # Update existing token
                existing_token.user_id = user_id
                existing_token.device_id = device_id
                existing_token.platform = platform
                existing_token.app_version = app_version
                existing_token.last_used = datetime.now()
            else:
                # Create new token
                device_token = DeviceToken(
                    user_id=user_id,
                    device_id=device_id,
                    platform=platform,
                    token=token,
                    app_version=app_version,
                )
                db.add(device_token)

            db.commit()
            logger.debug("Device token registered for user %s, device %s", user_id, device_id)
            return True

        except Exception as e:
            db.rollback()
            logger.error("Failed to register device token: %s", e)
            return False
        finally:
            db.close()

    async def unregister_device_token(self, user_id: str, device_id: str) -> bool:
        """
        Unregister a device token.

        Args:
            user_id: User ID
            device_id: Device ID to remove

        Returns:
            Success status
        """
        db = next(get_db())
        try:
            token = (
                db.query(DeviceToken)
                .filter(
                    DeviceToken.user_id == user_id, DeviceToken.device_id == device_id
                )
                .first()
            )

            if token:
                db.delete(token)
                db.commit()
                logger.debug("Device token unregistered for user %s, device %s" % (user_id, device_id)
                )
                return True
            

            logger.warning("Device token not found for user %s, device %s", user_id, device_id)
            return False

        except Exception as e:
            db.rollback()
            logger.error("Failed to unregister device token: %s", e)
            return False
        finally:
            db.close()

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user notification preferences.

        Args:
            user_id: User ID

        Returns:
            User preferences as dictionary
        """
        preferences = await self._get_user_preferences(user_id)
        if not preferences:
            return None

        return {
            "push_enabled": preferences.push_enabled,
            "push_application_submitted": preferences.push_application_submitted,
            "push_application_completed": preferences.push_application_completed,
            "push_application_failed": preferences.push_application_failed,
            "push_captcha_detected": preferences.push_captcha_detected,
            "push_job_match_found": preferences.push_job_match_found,
            "push_system_notification": preferences.push_system_notification,
            "email_enabled": preferences.email_enabled,
            "email_application_submitted": preferences.email_application_submitted,
            "email_application_completed": preferences.email_application_completed,
            "email_application_failed": preferences.email_application_failed,
            "email_captcha_detected": preferences.email_captcha_detected,
            "email_job_match_found": preferences.email_job_match_found,
            "email_system_notification": preferences.email_system_notification,
            "quiet_hours_enabled": preferences.quiet_hours_enabled,
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
        }

    async def update_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user notification preferences.

        Args:
            user_id: User ID
            preferences: Preferences dictionary

        Returns:
            Success status
        """
        db = next(get_db())
        try:
            existing_prefs = (
                db.query(UserNotificationPreferences)
                .filter(UserNotificationPreferences.user_id == user_id)
                .first()
            )

            if existing_prefs:
                # Update existing preferences
                for key, value in preferences.items():
                    if hasattr(existing_prefs, key):
                        setattr(existing_prefs, key, value)
            

            # Create new preferences
            new_prefs = UserNotificationPreferences(user_id=user_id, **preferences)
            db.add(new_prefs)

            db.commit()
            logger.debug("Notification preferences updated for user %s", user_id)
            return True

        except Exception as e:
            db.rollback()
            logger.error("Failed to update user preferences: %s", e)
            return False
        finally:
            db.close()

    async def _retry_operation(
        self, operation, max_retries: int = 3, delay: float = 1.0
    ):
        """Retry an operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error("Operation failed after %s attempts: %s", ('max_retries', 'e'))
                    raise

                wait_time = delay * (2**attempt)
                logger.warning("Operation failed (attempt %s/%s): %s. Retrying in %ss" % (attempt + 1, max_retries, e, wait_time)
                )
                await asyncio.sleep(wait_time)

    async def _send_push_notifications_safe(
        self, user_id: str, notification_type: str, message: str, metadata: Dict = None
    ):
        """Send push notifications with retry logic"""

        async def _operation():
            await self._send_push_notifications(
                user_id, notification_type, message, metadata
            )

        try:
            await self._retry_operation(_operation, max_retries=3, delay=1.0)
        except Exception as e:
            logger.error("Failed to send push notifications after retries: %s", e)
            # Don't raise - we don't want push notification failures to break the entire notification

    async def _send_email_notification_safe(
        self,
        user_id: str,
        notification_type: str,
        message: str,
        metadata: Dict = None,
        template: NotificationTemplate = None,
    ):
        """Send email notifications with retry logic"""

        async def _operation():
            await self._send_email_notification(
                user_id, notification_type, message, metadata, template
            )

        try:
            await self._retry_operation(_operation, max_retries=3, delay=2.0)
        except Exception as e:
            logger.error("Failed to send email notification after retries: %s", e)
            # Don't raise - we don't want email failures to break the entire notification

    def _validate_notification_data(
        self, user_id: str, notification_type: str, message: str
    ) -> bool:
        """Validate notification data"""
        if not user_id or not isinstance(user_id, str):
            logger.error("Invalid user_id")
            return False

        if not notification_type or not isinstance(notification_type, str):
            logger.error("Invalid notification_type")
            return False

        if not message or not isinstance(message, str):
            logger.error("Invalid message")
            return False

        return True

    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification delivery statistics"""
        db = next(get_db())
        try:
            # Get total notifications
            total_notifications = db.query(Notification).count()

            # Get delivered notifications
            delivered_notifications = (
                db.query(Notification).filter(Notification.delivered is True).count()
            )

            # Get notifications by type
            type_stats = (
                db.query(
                    Notification.type, db.func.count(Notification.id).label("count")
                )
                .group_by(Notification.type)
                .all()
            )

            # Get recent failures (last 24 hours)
            recent_failures = (
                db.query(Notification)
                .filter(
                    Notification.delivered is False,
                    Notification.created_at
                    >= datetime.now() - datetime.timedelta(hours=24),
                )
                .count()
            )

            return {
                "total_notifications": total_notifications,
                "delivered_notifications": delivered_notifications,
                "delivery_rate": (
                    (delivered_notifications / total_notifications * 100)
                    if total_notifications > 0
                    else 0
                ),
                "type_breakdown": {stat.type: stat.count for stat in type_stats},
                "recent_failures": recent_failures,
                "service_status": {
                    "apns": self.apns_enabled,
                    "fcm": self.fcm_enabled,
                    "email": self.email_enabled,
                },
            }

        except Exception as e:
            logger.error("Failed to get notification stats: %s", e)
            return {}
        finally:
            db.close()


# Global notification service instance
notification_service = NotificationService()
