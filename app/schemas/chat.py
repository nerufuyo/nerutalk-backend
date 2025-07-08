from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class ChatType(str, Enum):
    """Chat type enumeration."""
    PRIVATE = "private"
    GROUP = "group"


class ParticipantRole(str, Enum):
    """Participant role enumeration."""
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    GIF = "gif"
    LOCATION = "location"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message status enumeration."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# Chat Schemas
class ChatCreate(BaseModel):
    """Schema for creating a new chat."""
    
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    chat_type: ChatType
    participant_ids: List[uuid.UUID] = Field(..., min_items=1)
    
    @validator('name')
    def validate_group_chat_name(cls, v, values):
        """Validate that group chats have a name."""
        if values.get('chat_type') == ChatType.GROUP and not v:
            raise ValueError('Group chats must have a name')
        return v


class ChatUpdate(BaseModel):
    """Schema for updating chat information."""
    
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class ChatParticipantAdd(BaseModel):
    """Schema for adding participants to a chat."""
    
    user_ids: List[uuid.UUID] = Field(..., min_items=1)


class ChatParticipantUpdate(BaseModel):
    """Schema for updating participant role."""
    
    role: ParticipantRole


class ChatParticipantResponse(BaseModel):
    """Schema for chat participant response."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    role: ParticipantRole
    is_muted: bool
    is_pinned: bool
    joined_at: datetime
    
    # User information
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_online: bool
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Schema for chat response."""
    
    id: uuid.UUID
    name: Optional[str]
    description: Optional[str]
    chat_type: ChatType
    avatar_url: Optional[str]
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Additional information
    participant_count: int
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True


class ChatDetailResponse(ChatResponse):
    """Schema for detailed chat response with participants."""
    
    participants: List[ChatParticipantResponse]


# Message Schemas
class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    reply_to_id: Optional[uuid.UUID] = None
    metadata: Optional[str] = None  # JSON string for additional data
    
    @validator('content')
    def validate_text_content(cls, v, values):
        """Validate that text messages have content."""
        if values.get('message_type') == MessageType.TEXT and not v:
            raise ValueError('Text messages must have content')
        return v


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    
    content: str = Field(..., min_length=1)


class LocationData(BaseModel):
    """Schema for location message data."""
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    
    id: uuid.UUID
    content: Optional[str]
    message_type: MessageType
    status: MessageStatus
    file_url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    thumbnail_url: Optional[str]
    metadata: Optional[str]
    reply_to_id: Optional[uuid.UUID]
    is_edited: bool
    is_deleted: bool
    sender_id: uuid.UUID
    chat_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    
    # Sender information
    sender_username: str
    sender_full_name: Optional[str]
    sender_avatar_url: Optional[str]
    
    # Reply message info (if replying)
    reply_to_content: Optional[str] = None
    reply_to_sender: Optional[str] = None
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for paginated message list response."""
    
    messages: List[MessageResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class ChatListResponse(BaseModel):
    """Schema for chat list response."""
    
    chats: List[ChatResponse]
    total_count: int


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    """Schema for WebSocket message."""
    
    type: str  # message_sent, message_delivered, message_read, user_typing, etc.
    data: dict


class TypingIndicator(BaseModel):
    """Schema for typing indicator."""
    
    chat_id: uuid.UUID
    user_id: uuid.UUID
    is_typing: bool


class MessageDelivery(BaseModel):
    """Schema for message delivery confirmation."""
    
    message_id: uuid.UUID
    status: MessageStatus
    timestamp: datetime


class OnlineStatus(BaseModel):
    """Schema for user online status."""
    
    user_id: uuid.UUID
    is_online: bool
    last_seen: Optional[datetime] = None
