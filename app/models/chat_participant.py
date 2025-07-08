from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class ParticipantRole(enum.Enum):
    """Enum for participant roles in chat."""
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class ChatParticipant(Base):
    """
    Chat participant model for managing chat membership.
    
    Attributes:
        id: Unique participant record identifier (UUID)
        user_id: ID of the user
        chat_id: ID of the chat
        role: User's role in the chat
        is_muted: Whether the user has muted the chat
        is_pinned: Whether the user has pinned the chat
        last_read_message_id: ID of last message read by user
        joined_at: When the user joined the chat
        left_at: When the user left the chat (if applicable)
        is_active: Whether the user is still an active participant
    """
    
    __tablename__ = "chat_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    last_read_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    
    # Participant settings
    role = Column(Enum(ParticipantRole), nullable=False, default=ParticipantRole.MEMBER)
    is_muted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_participations")
    chat = relationship("Chat", back_populates="participants")
    last_read_message = relationship("Message")
    
    def __repr__(self):
        return f"<ChatParticipant(user_id={self.user_id}, chat_id={self.chat_id}, role={self.role})>"
