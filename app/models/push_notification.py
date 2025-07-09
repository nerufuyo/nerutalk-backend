"""
Device token model for push notifications.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum
import uuid
from app.core.database import Base


class DeviceType(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class DeviceToken(Base):
    """Device token model for push notifications."""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False, index=True)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    device_id = Column(String, nullable=True)  # Unique device identifier
    app_version = Column(String, nullable=True)
    
    # Device info
    device_name = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="device_tokens")


class PushNotification(Base):
    """Push notification model for tracking sent notifications."""
    __tablename__ = "push_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_token_id = Column(Integer, ForeignKey("device_tokens.id"), nullable=True)
    
    # Notification content
    title = Column(String(100), nullable=False)
    body = Column(String(500), nullable=False)
    data = Column(String, nullable=True)  # JSON string for additional data
    
    # Firebase specific
    fcm_message_id = Column(String, nullable=True)
    fcm_response = Column(String, nullable=True)  # JSON response from FCM
    
    # Notification type and category
    notification_type = Column(String(50), nullable=False)  # message, call, system, etc.
    category = Column(String(50), nullable=True)
    
    # Status
    is_sent = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    
    # Timestamps
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="push_notifications")
    device_token = relationship("DeviceToken")


class NotificationTemplate(Base):
    """Notification template model for predefined notification formats."""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    notification_type = Column(String(50), nullable=False)
    
    # Template content
    title_template = Column(String(200), nullable=False)
    body_template = Column(String(1000), nullable=False)
    
    # Localization
    language = Column(String(10), default="en")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
