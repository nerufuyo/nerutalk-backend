"""
Push notification service for handling notification business logic.
"""
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.push_notification import DeviceType
from app.repositories.push_notification_repository import (
    DeviceTokenRepository, PushNotificationRepository, NotificationTemplateRepository
)
from app.repositories.user_repository import UserRepository
from app.schemas.push_notification import (
    DeviceTokenCreate, DeviceTokenUpdate, DeviceTokenResponse,
    PushNotificationCreate, PushNotificationSend, PushNotificationBroadcast,
    PushNotificationResponse, NotificationStats,
    MessageNotificationData, CallNotificationData, SystemNotificationData
)
from app.utils.fcm_service import fcm_service
import asyncio

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for push notification operations."""

    def __init__(self, db: Session):
        self.db = db
        self.device_token_repo = DeviceTokenRepository(db)
        self.notification_repo = PushNotificationRepository(db)
        self.template_repo = NotificationTemplateRepository(db)
        self.user_repo = UserRepository(db)

    async def register_device_token(
        self,
        user_id: int,
        token_data: DeviceTokenCreate
    ) -> DeviceTokenResponse:
        """Register a new device token for push notifications."""
        try:
            # Validate token format
            if not fcm_service.validate_token(token_data.token):
                raise ValueError("Invalid FCM token format")
            
            # Create or update device token
            device_token = self.device_token_repo.create_device_token(user_id, token_data)
            
            logger.info(f"Device token registered for user {user_id}: {device_token.id}")
            return DeviceTokenResponse.from_orm(device_token)
            
        except Exception as e:
            logger.error(f"Error registering device token: {str(e)}")
            raise

    async def update_device_token(
        self,
        token_id: int,
        user_id: int,
        token_data: DeviceTokenUpdate
    ) -> Optional[DeviceTokenResponse]:
        """Update a device token."""
        try:
            # Verify token belongs to user
            device_token = self.device_token_repo.get_device_token_by_id(token_id)
            if not device_token or device_token.user_id != user_id:
                return None
            
            updated_token = self.device_token_repo.update_device_token(token_id, token_data)
            if updated_token:
                return DeviceTokenResponse.from_orm(updated_token)
            return None
            
        except Exception as e:
            logger.error(f"Error updating device token: {str(e)}")
            raise

    async def deactivate_device_token(self, token_id: int, user_id: int) -> bool:
        """Deactivate a device token."""
        try:
            device_token = self.device_token_repo.get_device_token_by_id(token_id)
            if not device_token or device_token.user_id != user_id:
                return False
            
            return self.device_token_repo.deactivate_device_token(token_id)
            
        except Exception as e:
            logger.error(f"Error deactivating device token: {str(e)}")
            raise

    async def get_user_device_tokens(self, user_id: int) -> List[DeviceTokenResponse]:
        """Get all device tokens for a user."""
        tokens = self.device_token_repo.get_device_tokens_by_user(user_id)
        return [DeviceTokenResponse.from_orm(token) for token in tokens]

    async def send_notification_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "system",
        data: Optional[Dict[str, Any]] = None,
        device_types: Optional[List[DeviceType]] = None
    ) -> List[PushNotificationResponse]:
        """Send a push notification to a specific user."""
        try:
            # Get user's device tokens
            device_tokens = self.device_token_repo.get_device_tokens_by_users(
                [user_id], device_types
            )
            
            if not device_tokens:
                logger.warning(f"No device tokens found for user {user_id}")
                return []
            
            notifications = []
            
            for device_token in device_tokens:
                # Create notification record
                notification_data = PushNotificationCreate(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    data=data
                )
                
                db_notification = self.notification_repo.create_notification(notification_data)
                
                # Send FCM notification
                success, message_id, error = await fcm_service.send_notification(
                    token=device_token.token,
                    title=title,
                    body=body,
                    data=data,
                    notification_type=notification_type
                )
                
                # Update notification status
                self.notification_repo.update_notification_status(
                    db_notification.id,
                    is_sent=success,
                    fcm_message_id=message_id,
                    error_message=error
                )
                
                # Update device token last used
                if success:
                    self.device_token_repo.update_last_used(device_token.id)
                
                notifications.append(PushNotificationResponse.from_orm(db_notification))
            
            logger.info(f"Sent {len(notifications)} notifications to user {user_id}")
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending notification to user: {str(e)}")
            raise

    async def send_notifications_to_users(
        self,
        notification_data: PushNotificationSend
    ) -> Dict[str, Any]:
        """Send push notifications to multiple users."""
        try:
            # Get device tokens for all users
            device_tokens = self.device_token_repo.get_device_tokens_by_users(
                notification_data.user_ids, notification_data.device_types
            )
            
            if not device_tokens:
                logger.warning(f"No device tokens found for users {notification_data.user_ids}")
                return {"success_count": 0, "failure_count": 0, "notifications": []}
            
            # Group tokens by user for notification records
            tokens_by_user = {}
            token_list = []
            
            for device_token in device_tokens:
                if device_token.user_id not in tokens_by_user:
                    tokens_by_user[device_token.user_id] = []
                tokens_by_user[device_token.user_id].append(device_token)
                token_list.append(device_token.token)
            
            # Create notification records
            notifications = []
            for user_id in tokens_by_user:
                notification_create = PushNotificationCreate(
                    user_id=user_id,
                    title=notification_data.title,
                    body=notification_data.body,
                    notification_type=notification_data.notification_type,
                    category=notification_data.category,
                    data=notification_data.data
                )
                db_notification = self.notification_repo.create_notification(notification_create)
                notifications.append(PushNotificationResponse.from_orm(db_notification))
            
            # Send multicast notification
            result = await fcm_service.send_multicast_notification(
                tokens=token_list,
                title=notification_data.title,
                body=notification_data.body,
                data=notification_data.data,
                notification_type=notification_data.notification_type
            )
            
            # Update notification statuses based on results
            for i, notification in enumerate(notifications):
                if i < len(result.get("results", [])):
                    fcm_result = result["results"][i]
                    success = "message_id" in fcm_result
                    message_id = fcm_result.get("message_id")
                    error = fcm_result.get("error")
                    
                    self.notification_repo.update_notification_status(
                        notification.id,
                        is_sent=success,
                        fcm_message_id=message_id,
                        error_message=error
                    )
            
            logger.info(
                f"Sent notifications to {len(notification_data.user_ids)} users: "
                f"{result['success_count']} success, {result['failure_count']} failures"
            )
            
            return {
                "success_count": result["success_count"],
                "failure_count": result["failure_count"],
                "notifications": notifications
            }
            
        except Exception as e:
            logger.error(f"Error sending notifications to users: {str(e)}")
            raise

    async def broadcast_notification(
        self,
        notification_data: PushNotificationBroadcast
    ) -> Dict[str, Any]:
        """Broadcast a notification to all users with active device tokens."""
        try:
            # Get all active device tokens
            all_users = self.user_repo.get_all_active_users()
            user_ids = [user.id for user in all_users]
            
            if not user_ids:
                logger.warning("No active users found for broadcast")
                return {"success_count": 0, "failure_count": 0, "notifications": []}
            
            send_data = PushNotificationSend(
                user_ids=user_ids,
                title=notification_data.title,
                body=notification_data.body,
                notification_type=notification_data.notification_type,
                category=notification_data.category,
                data=notification_data.data,
                device_types=notification_data.device_types
            )
            
            return await self.send_notifications_to_users(send_data)
            
        except Exception as e:
            logger.error(f"Error broadcasting notification: {str(e)}")
            raise

    async def send_message_notification(
        self,
        recipient_user_id: int,
        sender_name: str,
        message_data: MessageNotificationData,
        chat_name: Optional[str] = None
    ) -> List[PushNotificationResponse]:
        """Send a notification for a new message."""
        try:
            # Use template if available
            template = self.template_repo.get_template_by_name("new_message")
            
            if template:
                title = template.title_template.format(
                    sender_name=sender_name,
                    chat_name=chat_name or "Chat"
                )
                body = template.body_template.format(
                    sender_name=sender_name,
                    chat_name=chat_name or "Chat"
                )
            else:
                title = f"New message from {sender_name}"
                body = f"{sender_name}: {message_data.message_type}"
                if chat_name:
                    title = f"New message in {chat_name}"
            
            return await self.send_notification_to_user(
                user_id=recipient_user_id,
                title=title,
                body=body,
                notification_type="message",
                data=message_data.dict()
            )
            
        except Exception as e:
            logger.error(f"Error sending message notification: {str(e)}")
            raise

    async def send_call_notification(
        self,
        recipient_user_id: int,
        call_data: CallNotificationData
    ) -> List[PushNotificationResponse]:
        """Send a notification for an incoming call."""
        try:
            # Use template if available
            template = self.template_repo.get_template_by_name("incoming_call")
            
            if template:
                title = template.title_template.format(
                    caller_name=call_data.caller_name,
                    call_type=call_data.call_type
                )
                body = template.body_template.format(
                    caller_name=call_data.caller_name,
                    call_type=call_data.call_type
                )
            else:
                title = f"Incoming {call_data.call_type} call"
                body = f"{call_data.caller_name} is calling you"
            
            return await self.send_notification_to_user(
                user_id=recipient_user_id,
                title=title,
                body=body,
                notification_type="call",
                data=call_data.dict()
            )
            
        except Exception as e:
            logger.error(f"Error sending call notification: {str(e)}")
            raise

    async def send_system_notification(
        self,
        user_id: int,
        system_data: SystemNotificationData,
        title: Optional[str] = None,
        body: Optional[str] = None
    ) -> List[PushNotificationResponse]:
        """Send a system notification."""
        try:
            # Use template if available
            template = self.template_repo.get_template_by_name(f"system_{system_data.action}")
            
            if template:
                notification_title = template.title_template.format(**system_data.dict())
                notification_body = template.body_template.format(**system_data.dict())
            else:
                notification_title = title or "System Notification"
                notification_body = body or f"System action: {system_data.action}"
            
            return await self.send_notification_to_user(
                user_id=user_id,
                title=notification_title,
                body=notification_body,
                notification_type="system",
                data=system_data.dict()
            )
            
        except Exception as e:
            logger.error(f"Error sending system notification: {str(e)}")
            raise

    async def get_notification_stats(
        self, 
        user_id: Optional[int] = None, 
        days: int = 30
    ) -> NotificationStats:
        """Get notification statistics."""
        stats = self.notification_repo.get_notification_stats(user_id, days)
        return NotificationStats(**stats)

    async def process_pending_notifications(self) -> int:
        """Process pending scheduled notifications."""
        try:
            pending_notifications = self.notification_repo.get_pending_notifications()
            processed_count = 0
            
            for notification in pending_notifications:
                try:
                    # Get user's device tokens
                    device_tokens = self.device_token_repo.get_device_tokens_by_user(
                        notification.user_id
                    )
                    
                    if not device_tokens:
                        # Mark as failed - no device tokens
                        self.notification_repo.update_notification_status(
                            notification.id,
                            is_sent=False,
                            error_message="No active device tokens"
                        )
                        continue
                    
                    # Send to all user's devices
                    for device_token in device_tokens:
                        success, message_id, error = await fcm_service.send_notification(
                            token=device_token.token,
                            title=notification.title,
                            body=notification.body,
                            data=json.loads(notification.data) if notification.data else None,
                            notification_type=notification.notification_type
                        )
                        
                        # Update first successful send
                        if success and not notification.is_sent:
                            self.notification_repo.update_notification_status(
                                notification.id,
                                is_sent=True,
                                fcm_message_id=message_id
                            )
                            break
                        elif not success and not notification.is_sent:
                            self.notification_repo.update_notification_status(
                                notification.id,
                                is_sent=False,
                                error_message=error
                            )
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing notification {notification.id}: {str(e)}")
                    self.notification_repo.update_notification_status(
                        notification.id,
                        is_sent=False,
                        error_message=str(e)
                    )
            
            logger.info(f"Processed {processed_count} pending notifications")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing pending notifications: {str(e)}")
            raise

    async def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old notification data."""
        try:
            # Clean up old device tokens
            tokens_cleaned = self.device_token_repo.cleanup_old_tokens(days)
            
            # Note: In a real implementation, you might also want to clean up old notifications
            # but be careful to preserve data for analytics and user history
            
            logger.info(f"Cleaned up {tokens_cleaned} old device tokens")
            
            return {
                "device_tokens_cleaned": tokens_cleaned,
                "notifications_cleaned": 0  # Implement if needed
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            raise
