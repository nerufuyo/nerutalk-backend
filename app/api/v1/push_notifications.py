"""
Push notification API endpoints for the NeruTalk application.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.push_notification_service import PushNotificationService
from app.schemas.push_notification import (
    DeviceTokenCreate, DeviceTokenUpdate, DeviceTokenResponse,
    PushNotificationSend, PushNotificationBroadcast, PushNotificationResponse,
    NotificationStats, MessageNotificationData, CallNotificationData, SystemNotificationData
)
from app.schemas.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["push-notifications"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


def get_push_notification_service(db: Session = Depends(get_db)) -> PushNotificationService:
    """Get push notification service instance."""
    return PushNotificationService(db)


async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    # This would typically involve JWT token validation
    # For now, we'll use a placeholder implementation
    # In production, implement proper JWT validation
    pass


@router.post("/device-tokens", response_model=DeviceTokenResponse)
async def register_device_token(
    token_data: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Register a device token for push notifications.
    
    Args:
        token_data: Device token registration data
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        DeviceTokenResponse: Registered device token details
    """
    try:
        device_token = await notification_service.register_device_token(
            user_id=current_user.id,
            token_data=token_data
        )
        return device_token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.get("/device-tokens", response_model=List[DeviceTokenResponse])
async def get_device_tokens(
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Get all device tokens for the current user.
    
    Args:
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        List[DeviceTokenResponse]: List of user's device tokens
    """
    try:
        device_tokens = await notification_service.get_user_device_tokens(current_user.id)
        return device_tokens
    except Exception as e:
        logger.error(f"Error getting device tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device tokens"
        )


@router.put("/device-tokens/{token_id}", response_model=DeviceTokenResponse)
async def update_device_token(
    token_id: int,
    token_data: DeviceTokenUpdate,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Update a device token.
    
    Args:
        token_id: ID of the device token to update
        token_data: Update data for the device token
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        DeviceTokenResponse: Updated device token details
    """
    try:
        device_token = await notification_service.update_device_token(
            token_id=token_id,
            user_id=current_user.id,
            token_data=token_data
        )
        if not device_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found"
            )
        return device_token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device token"
        )


@router.delete("/device-tokens/{token_id}")
async def deactivate_device_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Deactivate a device token.
    
    Args:
        token_id: ID of the device token to deactivate
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        Success message
    """
    try:
        success = await notification_service.deactivate_device_token(
            token_id=token_id,
            user_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found"
            )
        return {"message": "Device token deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate device token"
        )


@router.post("/send")
async def send_notifications(
    notification_data: PushNotificationSend,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Send push notifications to specific users.
    
    Args:
        notification_data: Notification data and target users
        current_user: Current authenticated user (must be admin)
        notification_service: Push notification service instance
        
    Returns:
        Notification sending results
    """
    try:
        # Note: In production, add admin role check here
        result = await notification_service.send_notifications_to_users(notification_data)
        return result
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notifications"
        )


@router.post("/broadcast")
async def broadcast_notification(
    notification_data: PushNotificationBroadcast,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Broadcast a notification to all users.
    
    Args:
        notification_data: Broadcast notification data
        current_user: Current authenticated user (must be admin)
        notification_service: Push notification service instance
        
    Returns:
        Broadcast results
    """
    try:
        # Note: In production, add admin role check here
        result = await notification_service.broadcast_notification(notification_data)
        return result
    except Exception as e:
        logger.error(f"Error broadcasting notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast notification"
        )


@router.post("/message")
async def send_message_notification(
    recipient_user_id: int,
    sender_name: str,
    message_data: MessageNotificationData,
    chat_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Send a message notification.
    
    Args:
        recipient_user_id: ID of the user to notify
        sender_name: Name of the message sender
        message_data: Message notification data
        chat_name: Optional chat name
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        List of sent notifications
    """
    try:
        notifications = await notification_service.send_message_notification(
            recipient_user_id=recipient_user_id,
            sender_name=sender_name,
            message_data=message_data,
            chat_name=chat_name
        )
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Error sending message notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message notification"
        )


@router.post("/call")
async def send_call_notification(
    recipient_user_id: int,
    call_data: CallNotificationData,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Send a call notification.
    
    Args:
        recipient_user_id: ID of the user to notify
        call_data: Call notification data
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        List of sent notifications
    """
    try:
        notifications = await notification_service.send_call_notification(
            recipient_user_id=recipient_user_id,
            call_data=call_data
        )
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Error sending call notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send call notification"
        )


@router.post("/system")
async def send_system_notification(
    user_id: int,
    system_data: SystemNotificationData,
    title: Optional[str] = None,
    body: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Send a system notification.
    
    Args:
        user_id: ID of the user to notify
        system_data: System notification data
        title: Optional custom title
        body: Optional custom body
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        List of sent notifications
    """
    try:
        notifications = await notification_service.send_system_notification(
            user_id=user_id,
            system_data=system_data,
            title=title,
            body=body
        )
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Error sending system notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send system notification"
        )


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Get notification statistics for the current user.
    
    Args:
        days: Number of days to include in statistics
        current_user: Current authenticated user
        notification_service: Push notification service instance
        
    Returns:
        NotificationStats: User's notification statistics
    """
    try:
        stats = await notification_service.get_notification_stats(
            user_id=current_user.id,
            days=days
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification statistics"
        )


@router.get("/stats/admin", response_model=NotificationStats)
async def get_admin_notification_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    notification_service: PushNotificationService = Depends(get_push_notification_service)
):
    """
    Get global notification statistics (admin only).
    
    Args:
        days: Number of days to include in statistics
        current_user: Current authenticated user (must be admin)
        notification_service: Push notification service instance
        
    Returns:
        NotificationStats: Global notification statistics
    """
    try:
        # Note: In production, add admin role check here
        stats = await notification_service.get_notification_stats(
            user_id=None,  # Global stats
            days=days
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting admin notification stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification statistics"
        )
