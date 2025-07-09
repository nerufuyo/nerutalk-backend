from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class MessageType(enum.Enum):
    """Enum for message types."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    GIF = "gif"
    LOCATION = "location"
    SYSTEM = "system"


class MessageStatus(enum.Enum):
    """Enum for message status."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class Message(Base):
    """
    Message model for storing chat messages.
    
    Attributes:
        id: Unique message identifier (UUID)
        content: Message content/text
        message_type: Type of message (text, image, etc.)
        status: Message delivery status
        file_url: URL to attached file (if any)
        file_name: Original file name
        file_size: File size in bytes
        thumbnail_url: URL to thumbnail (for images/videos)
        message_metadata: Additional message metadata (JSON)
        reply_to_id: ID of message being replied to
        is_edited: Whether the message has been edited
        is_deleted: Whether the message is deleted
        sender_id: ID of user who sent the message
        chat_id: ID of chat this message belongs to
        created_at: Message creation timestamp
        updated_at: Last message update timestamp
        delivered_at: Message delivery timestamp
        read_at: Message read timestamp
    """
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    content = Column(Text, nullable=True)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    status = Column(Enum(MessageStatus), nullable=False, default=MessageStatus.SENT)
    
    # File attachments
    file_url = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    
    # Message metadata (JSON field for additional data like location coordinates, sticker info, etc.)
    message_metadata = Column(Text, nullable=True)  # Store as JSON string
    
    # Reply functionality
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    
    # Message status flags
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Foreign keys
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sender = relationship("User", back_populates="sent_messages")
    chat = relationship("Chat", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id])
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, chat_id={self.chat_id}, type={self.message_type})>"
