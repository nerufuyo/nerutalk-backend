"""
Push notification repository for database operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from app.models.push_notification import (
    DeviceToken, PushNotification, NotificationTemplate, DeviceType
)
from app.schemas.push_notification import (
    DeviceTokenCreate, DeviceTokenUpdate, PushNotificationCreate,
    NotificationTemplateCreate, NotificationTemplateUpdate
)


class DeviceTokenRepository:
    """Repository for device token operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_device_token(self, user_id: int, token_data: DeviceTokenCreate) -> DeviceToken:
        """Create a new device token."""
        # Check if token already exists for this user and device
        existing_token = (
            self.db.query(DeviceToken)
            .filter(
                and_(
                    DeviceToken.user_id == user_id,
                    DeviceToken.token == token_data.token
                )
            )
            .first()
        )
        
        if existing_token:
            # Update existing token
            for field, value in token_data.dict(exclude_unset=True).items():
                setattr(existing_token, field, value)
            existing_token.is_active = True
            existing_token.last_used = datetime.utcnow()
            existing_token.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_token)
            return existing_token
        
        # Create new token
        db_token = DeviceToken(
            user_id=user_id,
            **token_data.dict()
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def get_device_token_by_id(self, token_id: int) -> Optional[DeviceToken]:
        """Get a device token by ID."""
        return self.db.query(DeviceToken).filter(DeviceToken.id == token_id).first()

    def get_device_tokens_by_user(self, user_id: int, active_only: bool = True) -> List[DeviceToken]:
        """Get all device tokens for a user."""
        query = self.db.query(DeviceToken).filter(DeviceToken.user_id == user_id)
        if active_only:
            query = query.filter(DeviceToken.is_active == True)
        return query.order_by(desc(DeviceToken.last_used)).all()

    def get_device_tokens_by_users(
        self, 
        user_ids: List[int], 
        device_types: Optional[List[DeviceType]] = None,
        active_only: bool = True
    ) -> List[DeviceToken]:
        """Get device tokens for multiple users."""
        query = self.db.query(DeviceToken).filter(DeviceToken.user_id.in_(user_ids))
        
        if active_only:
            query = query.filter(DeviceToken.is_active == True)
        
        if device_types:
            query = query.filter(DeviceToken.device_type.in_(device_types))
            
        return query.all()

    def update_device_token(self, token_id: int, token_data: DeviceTokenUpdate) -> Optional[DeviceToken]:
        """Update a device token."""
        db_token = self.get_device_token_by_id(token_id)
        if not db_token:
            return None

        update_data = token_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_token, field, value)

        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def update_last_used(self, token_id: int) -> bool:
        """Update the last used timestamp for a device token."""
        db_token = self.get_device_token_by_id(token_id)
        if not db_token:
            return False
            
        db_token.last_used = datetime.utcnow()
        db_token.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def deactivate_device_token(self, token_id: int) -> bool:
        """Deactivate a device token."""
        db_token = self.get_device_token_by_id(token_id)
        if not db_token:
            return False
            
        db_token.is_active = False
        db_token.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def delete_device_token(self, token_id: int) -> bool:
        """Delete a device token."""
        db_token = self.get_device_token_by_id(token_id)
        if not db_token:
            return False

        self.db.delete(db_token)
        self.db.commit()
        return True

    def cleanup_old_tokens(self, days: int = 90) -> int:
        """Clean up old inactive device tokens."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = (
            self.db.query(DeviceToken)
            .filter(
                and_(
                    DeviceToken.is_active == False,
                    DeviceToken.updated_at < cutoff_date
                )
            )
            .delete()
        )
        
        self.db.commit()
        return deleted_count


class PushNotificationRepository:
    """Repository for push notification operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, notification_data: PushNotificationCreate) -> PushNotification:
        """Create a new push notification record."""
        db_notification = PushNotification(**notification_data.dict())
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)
        return db_notification

    def get_notification_by_id(self, notification_id: int) -> Optional[PushNotification]:
        """Get a push notification by ID."""
        return (
            self.db.query(PushNotification)
            .filter(PushNotification.id == notification_id)
            .first()
        )

    def get_notifications_by_user(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[PushNotification]:
        """Get push notifications for a user."""
        return (
            self.db.query(PushNotification)
            .filter(PushNotification.user_id == user_id)
            .order_by(desc(PushNotification.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_notification_status(
        self,
        notification_id: int,
        is_sent: Optional[bool] = None,
        is_delivered: Optional[bool] = None,
        is_read: Optional[bool] = None,
        fcm_message_id: Optional[str] = None,
        fcm_response: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[PushNotification]:
        """Update notification status."""
        db_notification = self.get_notification_by_id(notification_id)
        if not db_notification:
            return None

        current_time = datetime.utcnow()
        
        if is_sent is not None:
            db_notification.is_sent = is_sent
            if is_sent:
                db_notification.sent_at = current_time
        
        if is_delivered is not None:
            db_notification.is_delivered = is_delivered
            if is_delivered:
                db_notification.delivered_at = current_time
        
        if is_read is not None:
            db_notification.is_read = is_read
            if is_read:
                db_notification.read_at = current_time
        
        if fcm_message_id:
            db_notification.fcm_message_id = fcm_message_id
        
        if fcm_response:
            db_notification.fcm_response = fcm_response
        
        if error_message:
            db_notification.error_message = error_message

        self.db.commit()
        self.db.refresh(db_notification)
        return db_notification

    def get_pending_notifications(self, limit: int = 100) -> List[PushNotification]:
        """Get pending notifications to be sent."""
        current_time = datetime.utcnow()
        
        return (
            self.db.query(PushNotification)
            .filter(
                and_(
                    PushNotification.is_sent == False,
                    or_(
                        PushNotification.scheduled_at.is_(None),
                        PushNotification.scheduled_at <= current_time
                    )
                )
            )
            .order_by(PushNotification.created_at)
            .limit(limit)
            .all()
        )

    def get_notification_stats(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get notification statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        base_query = self.db.query(PushNotification).filter(
            PushNotification.created_at >= start_date
        )
        
        if user_id:
            base_query = base_query.filter(PushNotification.user_id == user_id)
        
        stats = (
            base_query
            .with_entities(
                func.count(PushNotification.id).label("total_sent"),
                func.sum(
                    func.case(
                        (PushNotification.is_delivered == True, 1),
                        else_=0
                    )
                ).label("total_delivered"),
                func.sum(
                    func.case(
                        (PushNotification.is_read == True, 1),
                        else_=0
                    )
                ).label("total_read"),
                func.sum(
                    func.case(
                        (PushNotification.error_message.isnot(None), 1),
                        else_=0
                    )
                ).label("total_failed")
            )
            .first()
        )
        
        total_sent = stats.total_sent or 0
        total_delivered = stats.total_delivered or 0
        total_read = stats.total_read or 0
        total_failed = stats.total_failed or 0
        
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        read_rate = (total_read / total_delivered * 100) if total_delivered > 0 else 0
        
        # Get device type breakdown
        device_breakdown = {}
        device_stats = (
            self.db.query(
                DeviceToken.device_type,
                func.count(PushNotification.id).label("count")
            )
            .join(PushNotification, DeviceToken.id == PushNotification.device_token_id)
            .filter(PushNotification.created_at >= start_date)
            .group_by(DeviceToken.device_type)
            .all()
        )
        
        for device_type, count in device_stats:
            device_breakdown[device_type.value] = count
        
        # Get notification type breakdown
        type_breakdown = {}
        type_stats = (
            base_query
            .with_entities(
                PushNotification.notification_type,
                func.count(PushNotification.id).label("count")
            )
            .group_by(PushNotification.notification_type)
            .all()
        )
        
        for notification_type, count in type_stats:
            type_breakdown[notification_type] = count
        
        return {
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_read": total_read,
            "total_failed": total_failed,
            "delivery_rate": round(delivery_rate, 2),
            "read_rate": round(read_rate, 2),
            "device_breakdown": device_breakdown,
            "notification_type_breakdown": type_breakdown
        }


class NotificationTemplateRepository:
    """Repository for notification template operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_template(self, template_data: NotificationTemplateCreate) -> NotificationTemplate:
        """Create a new notification template."""
        db_template = NotificationTemplate(**template_data.dict())
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def get_template_by_id(self, template_id: int) -> Optional[NotificationTemplate]:
        """Get a notification template by ID."""
        return (
            self.db.query(NotificationTemplate)
            .filter(NotificationTemplate.id == template_id)
            .first()
        )

    def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get a notification template by name."""
        return (
            self.db.query(NotificationTemplate)
            .filter(NotificationTemplate.name == name)
            .first()
        )

    def get_templates(
        self, 
        notification_type: Optional[str] = None,
        language: Optional[str] = None,
        active_only: bool = True
    ) -> List[NotificationTemplate]:
        """Get notification templates with optional filtering."""
        query = self.db.query(NotificationTemplate)
        
        if notification_type:
            query = query.filter(NotificationTemplate.notification_type == notification_type)
        
        if language:
            query = query.filter(NotificationTemplate.language == language)
        
        if active_only:
            query = query.filter(NotificationTemplate.is_active == True)
        
        return query.order_by(NotificationTemplate.name).all()

    def update_template(
        self, 
        template_id: int, 
        template_data: NotificationTemplateUpdate
    ) -> Optional[NotificationTemplate]:
        """Update a notification template."""
        db_template = self.get_template_by_id(template_id)
        if not db_template:
            return None

        update_data = template_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_template, field, value)

        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def delete_template(self, template_id: int) -> bool:
        """Delete a notification template."""
        db_template = self.get_template_by_id(template_id)
        if not db_template:
            return False

        self.db.delete(db_template)
        self.db.commit()
        return True
