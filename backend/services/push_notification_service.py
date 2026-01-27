"""
Push Notification Service

Handles push notification delivery for iOS (APNs) and Android (FCM).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from backend.config import settings
from backend.db.database import async_session
from backend.db.models import DeviceToken, Notification, User
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Device platform types"""

    IOS = "ios"
    ANDROID = "android"


@dataclass
class PushPayload:
    """Push notification payload"""

    title: str
    body: str
    data: Dict[str, str] = None
    badge: Optional[int] = None
    sound: Optional[str] = None
    image_url: Optional[str] = None
    ttl: int = 86400  # 24 hours
    priority: str = "high"
    collapse_key: Optional[str] = None


@dataclass
class PushResult:
    """Result of push notification sending"""

    success: bool
    platform: Platform
    device_token: str
    message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class APNsClient:
    """Apple Push Notification service client"""

    def __init__(self, key_id: str, team_id: str, bundle_id: str, private_key: str):
        self.key_id = key_id
        self.team_id = team_id
        self.bundle_id = bundle_id
        self.private_key = private_key
        self.base_url = "https://api.push.apple.com"

    async def send(
        self,
        device_token: str,
        payload: PushPayload,
        topic: Optional[str] = None,
    ) -> PushResult:
        """Send push notification via APNs"""
        url = f"{self.base_url}/v2/bundle/{self.bundle_id}/message"

        headers = {
            "authorization": f"bearer {await self._get_access_token()}",
            "apns-topic": topic or self.bundle_id,
            "apns-priority": str(10 if payload.priority == "high" else 5),
            "apns-ttl": str(payload.ttl),
        }

        if payload.collapse_key:
            headers["apns-collapse-id"] = payload.collapse_key

        aps_payload = {
            "alert": {
                "title": payload.title,
                "body": payload.body,
            },
            "sound": payload.sound or "default",
        }

        if payload.badge is not None:
            aps_payload["badge"] = payload.badge

        if payload.data:
            aps_payload["custom_data"] = payload.data

        body = {
            "aps": aps_payload,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=30.0,
                )

            if response.status_code == 200:
                apns_id = response.headers.get("apns-id")
                return PushResult(
                    success=True,
                    platform=Platform.IOS,
                    device_token=device_token,
                    message_id=apns_id,
                )
            error_data = response.json()
            return PushResult(
                success=False,
                    platform=Platform.IOS,
                    device_token=device_token,
                    error_code=error_data.get("reason"),
                    error_message=str(error_data),
                )
        except Exception as e:
            logger.error("APNs send failed: %s", e)
            return PushResult(
                success=False,
                platform=Platform.IOS,
                device_token=device_token,
                error_message=str(e),
            )

    async def _get_access_token(self) -> str:
        """Generate JWT for APNs authentication"""
        # In production, use proper JWT signing
        # This is a placeholder for the token generation logic
        return "placeholder_token"


class FCMClient:
    """Firebase Cloud Messaging client"""

    def __init__(self, project_id: str, credentials: Dict[str, Any]):
        self.project_id = project_id
        self.credentials = credentials
        self.base_url = "https://fcm.googleapis.com/v1/projects"

    async def send(
        self,
        device_token: str,
        payload: PushPayload,
    ) -> PushResult:
        """Send push notification via FCM"""
        url = f"{self.base_url}/{self.project_id}/messages:send"

        message = {
            "token": device_token,
            "notification": {
                "title": payload.title,
                "body": payload.body,
            },
            "android": {
                "priority": payload.priority,
                "notification": {
                    "sound": payload.sound or "default",
                },
                "ttl": f"{payload.ttl}s",
            },
        }

        if payload.data:
            message["data"] = payload.data

        if payload.image_url:
            message["notification"]["image"] = payload.image_url

        if payload.collapse_key:
            message["android"]["collapse_key"] = payload.collapse_key

        try:
            access_token = await self._get_access_token()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={"message": message},
                    timeout=30.0,
                )

            if response.status_code == 200:
                response_data = response.json()
                return PushResult(
                    success=True,
                    platform=Platform.ANDROID,
                    device_token=device_token,
                    message_id=response_data.get("name"),
                )
            error_data = response.json()
                return PushResult(
                    success=False,
                    platform=Platform.ANDROID,
                    device_token=device_token,
                    error_code=error_data.get("error", {}).get("code"),
                    error_message=str(error_data),
                )
        except Exception as e:
            logger.error("FCM send failed: %s", e)
            return PushResult(
                success=False,
                platform=Platform.ANDROID,
                device_token=device_token,
                error_message=str(e),
            )

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for FCM"""
        # In production, use proper OAuth2 token generation
        return "placeholder_token"


class PushNotificationService:
    """
    Unified push notification service for iOS and Android
    """

    def __init__(self):
        self.apns = APNsClient(
            key_id=settings.APPLE_KEY_ID,
            team_id=settings.APPLE_TEAM_ID,
            bundle_id=settings.APPLE_BUNDLE_ID,
            private_key=settings.APPLE_PRIVATE_KEY,
        )
        self.fcm = FCMClient(
            project_id=settings.FIREBASE_PROJECT_ID,
            credentials={},
        )
        self.notification_service = NotificationService()

    async def send_notification(
        self,
        user_id: str,
        payload: PushPayload,
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[PushResult]:
        """
        Send push notification to all user's devices

        Args:
            user_id: User ID to send notification to
            payload: Push notification payload
            notification_type: Type of notification
            metadata: Additional metadata for the notification

        Returns:
            List of push results for each device
        """
        async with async_session() as session:
            # Get user's device tokens
            device_tokens = await session.execute(
                DeviceToken.__table__.select().where(DeviceToken.user_id == user_id)
            )
            tokens = device_tokens.fetchall()

        if not tokens:
            logger.info("No device tokens found for user %s", user_id)
            return []

        # Create in-app notification
        notification = await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=payload.title,
            message=payload.body,
            metadata={
                **(payload.data or {}),
                **(metadata or {}),
            },
        )

        # Send to all devices
        results = []
        for token in tokens:
            if token.platform == Platform.IOS.value:
                result = await self.apns.send(token.token, payload)
            

            result = await self.fcm.send(token.token, payload)

        results.append(result)

            # Update device token if invalid
            if not result.success and result.error_code in (
                "Unregistered",
                "InvalidRegistration",
            ):
                await self._remove_device_token(token.token)

        # Update notification delivery status
        if notification:
            notification.delivered = any(r.success for r in results)
            async with async_session() as session:
                await session.commit()

        return results

    async def send_bulk_notifications(
        self,
        user_ids: List[str],
        payload: PushPayload,
        notification_type: str,
    ) -> Dict[str, List[PushResult]]:
        """
        Send push notification to multiple users

        Args:
            user_ids: List of user IDs
            payload: Push notification payload
            notification_type: Type of notification

        Returns:
            Dictionary mapping user_id to list of push results
        """
        results = {}

        # Process in batches to avoid overwhelming the services
        batch_size = 100
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i : i + batch_size]
            tasks = [
                self.send_notification(
                    user_id=user_id,
                    payload=payload,
                    notification_type=notification_type,
                )
                for user_id in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for user_id, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error("Failed to send to %s: %s", ('user_id', 'result'))
                    results[user_id] = []
                

                results[user_id] = result

        return results

    async def _remove_device_token(self, token: str) -> None:
        """Remove invalid device token from database"""
        async with async_session() as session:
            await session.execute(
                DeviceToken.__table__.delete().where(DeviceToken.token == token)
            )
            await session.commit()

    async def register_device(
        self,
        user_id: str,
        device_id: str,
        platform: Platform,
        token: str,
        app_version: Optional[str] = None,
    ) -> DeviceToken:
        """
        Register or update device token

        Args:
            user_id: User ID
            device_id: Device identifier
            platform: Device platform (ios/android)
            token: Push notification token
            app_version: App version

        Returns:
            Created or updated DeviceToken
        """
        async with async_session() as session:
            # Check if device already registered
            existing = await session.execute(
                DeviceToken.__table__.select().where(DeviceToken.device_id == device_id)
            )
            device = existing.fetchone()

            if device:
                # Update existing token
                await session.execute(
                    DeviceToken.__table__.update()
                    .where(DeviceToken.id == device.id)
                    .values(
                        token=token,
                        platform=platform.value,
                        app_version=app_version,
                        last_used=datetime.now(timezone.utc),
                    )
                )
            

            # Create new token
            device = DeviceToken(
                user_id=user_id,
                device_id=device_id,
                platform=platform.value,
                token=token,
                app_version=app_version,
            )
            session.add(device)

        await session.commit()
            return device

    async def unregister_device(self, device_id: str) -> bool:
        """
        Unregister device token

        Args:
            device_id: Device identifier

        Returns:
            True if device was removed
        """
        async with async_session() as session:
            result = await session.execute(
                DeviceToken.__table__.delete().where(DeviceToken.device_id == device_id)
            )
            await session.commit()
            return result.rowcount > 0
