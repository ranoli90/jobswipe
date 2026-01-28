"""
Notifications API Router

Handles user notification endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.routers.auth import get_current_user, get_current_admin_user
from backend.db.database import get_db
from backend.db.models import User
from backend.services.notification_service import notification_service

router = APIRouter()


@router.get("/")
async def get_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user notifications.

    Args:
        limit: Maximum number of notifications to return (default: 50)

    Returns:
        List of user notifications
    """
    try:
        notifications = await notification_service.get_user_notifications(
            str(current_user.id), limit
        )
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get notifications: {str(e)}"
        )


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as read.

    Args:
        notification_id: ID of the notification to mark as read
    """
    try:
        await notification_service.mark_notification_read(
            str(current_user.id), notification_id
        )
        return {"message": "Notification marked as read"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get count of unread notifications.

    Returns:
        Count of unread notifications
    """
    try:
        notifications = await notification_service.get_user_notifications(
            str(current_user.id), 1000  # Get many to count unread
        )
        unread_count = sum(1 for n in notifications if not n["read"])
        return {"unread_count": unread_count}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get unread count: {str(e)}"
        )


@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Mark all notifications as read for the current user.
    """
    try:
        # Get all unread notifications and mark them as read
        notifications = await notification_service.get_user_notifications(
            str(current_user.id), 1000
        )
        unread_notifications = [n for n in notifications if not n["read"]]

        for notification in unread_notifications:
            await notification_service.mark_notification_read(
                str(current_user.id), notification["id"]
            )

        return {"message": f"Marked {len(unread_notifications)} notifications as read"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark all notifications as read: {str(e)}",
        )


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get user notification preferences.

    Returns:
        User notification preferences
    """
    try:
        preferences = await notification_service.get_user_preferences(
            str(current_user.id)
        )
        if preferences is None:
            # Return default preferences
            preferences = {
                "push_enabled": True,
                "push_application_submitted": True,
                "push_application_completed": True,
                "push_application_failed": True,
                "push_captcha_detected": True,
                "push_job_match_found": True,
                "push_system_notification": True,
                "email_enabled": True,
                "email_application_submitted": False,
                "email_application_completed": True,
                "email_application_failed": True,
                "email_captcha_detected": True,
                "email_job_match_found": True,
                "email_system_notification": True,
                "quiet_hours_enabled": False,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
            }
        return {"preferences": preferences}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification preferences: {str(e)}"
        )


@router.put("/preferences")
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user notification preferences.

    Args:
        preferences: Notification preferences to update
    """
    try:
        success = await notification_service.update_user_preferences(
            str(current_user.id), preferences
        )
        if success:
            return {"message": "Notification preferences updated successfully"}
        

        raise HTTPException(status_code=500, detail="Failed to update preferences")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update notification preferences: {str(e)}",
        )


@router.post("/device-token")
async def register_device_token(
    device_id: str,
    platform: str,
    token: str,
    app_version: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a device token for push notifications.

    Args:
        device_id: Unique device identifier
        platform: Device platform ('ios' or 'android')
        token: Push notification token
        app_version: App version (optional)
    """
    try:
        if platform not in ["ios", "android"]:
            raise HTTPException(
                status_code=400, detail="Platform must be 'ios' or 'android'"
            )

        success = await notification_service.register_device_token(
            str(current_user.id), device_id, platform, token, app_version
        )

        if success:
            return {"message": "Device token registered successfully"}
        

        raise HTTPException(
            status_code=500, detail="Failed to register device token"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register device token: {str(e)}"
        )


@router.delete("/device-token/{device_id}")
async def unregister_device_token(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unregister a device token.

    Args:
        device_id: Device ID to unregister
    """
    try:
        success = await notification_service.unregister_device_token(
            str(current_user.id), device_id
        )

        if success:
            return {"message": "Device token unregistered successfully"}
        

        raise HTTPException(status_code=404, detail="Device token not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to unregister device token: {str(e)}"
        )


@router.get("/stats")
async def get_notification_stats(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """
    Get notification delivery statistics (admin only).

    Returns:
        Notification statistics and service status
    """
    try:
        stats = await notification_service.get_notification_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification stats: {str(e)}"
        )
