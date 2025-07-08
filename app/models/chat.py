from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class ChatType(enum.Enum):
    """Enum for chat types."""
    PRIVATE = "private"
    GROUP = "group"


class Chat(Base):
    """
    Chat model for storing chat room information.
    
    Attributes:
        id: Unique chat identifier (UUID)
        name: Chat name (for group chats)
        description: Chat description
        chat_type: Type of chat (private or group)
        avatar_url: URL to chat avatar image
        is_active: Whether the chat is active
        created_by: ID of user who created the chat
        created_at: Chat creation timestamp
        updated_at: Last chat update timestamp
    """
    
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=True)  # For group chats
    description = Column(Text, nullable=True)
    chat_type = Column(Enum(ChatType), nullable=False, default=ChatType.PRIVATE)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Foreign keys
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    participants = relationship("ChatParticipant", back_populates="chat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, name='{self.name}', type={self.chat_type})>"
