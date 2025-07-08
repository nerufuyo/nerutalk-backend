"""
Push notification schemas for request/response data validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.push_notification import DeviceType


class DeviceTokenBase(BaseModel):
    """Base schema for device tokens."""
    token: str = Field(..., min_length=1, max_length=500)
    device_type: DeviceType
    device_id: Optional[str] = None
    app_version: Optional[str] = None
    device_name: Optional[str] = None
    os_version: Optional[str] = None


class DeviceTokenCreate(DeviceTokenBase):
    """Schema for creating a device token."""
    pass


class DeviceTokenUpdate(BaseModel):
    """Schema for updating a device token."""
    token: Optional[str] = None
    device_id: Optional[str] = None
    app_version: Optional[str] = None
    device_name: Optional[str] = None
    os_version: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceTokenResponse(DeviceTokenBase):
    """Schema for device token response."""
    id: int
    user_id: int
    is_active: bool
    last_used: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PushNotificationBase(BaseModel):
    """Base schema for push notifications."""
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    notification_type: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    data: Optional[Dict[str, Any]] = None


class PushNotificationCreate(PushNotificationBase):
    """Schema for creating a push notification."""
    user_id: int
    device_token_ids: Optional[List[int]] = None  # Specific device tokens to send to
    scheduled_at: Optional[datetime] = None


class PushNotificationSend(BaseModel):
    """Schema for sending immediate push notifications."""
    user_ids: List[int] = Field(..., min_items=1)
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    notification_type: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    data: Optional[Dict[str, Any]] = None
    device_types: Optional[List[DeviceType]] = None  # Filter by device types


class PushNotificationBroadcast(BaseModel):
    """Schema for broadcasting notifications to all users."""
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    notification_type: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    data: Optional[Dict[str, Any]] = None
    device_types: Optional[List[DeviceType]] = None


class PushNotificationResponse(PushNotificationBase):
    """Schema for push notification response."""
    id: int
    user_id: int
    device_token_id: Optional[int] = None
    fcm_message_id: Optional[str] = None
    is_sent: bool
    is_delivered: bool
    is_read: bool
    error_message: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationTemplateBase(BaseModel):
    """Base schema for notification templates."""
    name: str = Field(..., min_length=1, max_length=100)
    notification_type: str = Field(..., min_length=1, max_length=50)
    title_template: str = Field(..., min_length=1, max_length=200)
    body_template: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en", max_length=10)


class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema for creating a notification template."""
    pass


class NotificationTemplateUpdate(BaseModel):
    """Schema for updating a notification template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    notification_type: Optional[str] = Field(None, min_length=1, max_length=50)
    title_template: Optional[str] = Field(None, min_length=1, max_length=200)
    body_template: Optional[str] = Field(None, min_length=1, max_length=1000)
    language: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    """Schema for notification template response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Schema for notification statistics."""
    total_sent: int
    total_delivered: int
    total_read: int
    total_failed: int
    delivery_rate: float  # Percentage
    read_rate: float  # Percentage
    device_breakdown: Dict[str, int]  # Device type breakdown
    notification_type_breakdown: Dict[str, int]


class MessageNotificationData(BaseModel):
    """Schema for message notification data."""
    message_id: str
    chat_id: str
    sender_name: str
    sender_avatar: Optional[str] = None
    message_type: str = "text"
    chat_name: Optional[str] = None


class CallNotificationData(BaseModel):
    """Schema for call notification data."""
    call_id: int
    caller_id: str
    caller_name: str
    caller_avatar: Optional[str] = None
    call_type: str = "video"  # video or audio
    channel_name: str


class SystemNotificationData(BaseModel):
    """Schema for system notification data."""
    action: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    deep_link: Optional[str] = None


# Template variable schemas for different notification types
class MessageNotificationTemplate(BaseModel):
    """Template variables for message notifications."""
    sender_name: str
    chat_name: Optional[str] = None
    message_preview: str


class CallNotificationTemplate(BaseModel):
    """Template variables for call notifications."""
    caller_name: str
    call_type: str = "video"


class SystemNotificationTemplate(BaseModel):
    """Template variables for system notifications."""
    user_name: Optional[str] = None
    action: str
    resource: Optional[str] = None
