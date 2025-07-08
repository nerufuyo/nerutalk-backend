from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class User(Base):
    """
    User model for storing user account information.
    
    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique)
        username: User's username (unique)
        hashed_password: Hashed password for authentication
        full_name: User's full name
        avatar_url: URL to user's profile picture
        bio: User's bio/description
        phone_number: User's phone number
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        is_online: Whether the user is currently online
        last_seen: Timestamp of user's last activity
        created_at: Account creation timestamp
        updated_at: Last account update timestamp
    """
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)
    
    # Timestamps
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    created_chats = relationship("Chat", back_populates="creator")
    sent_messages = relationship("Message", back_populates="sender")
    chat_participations = relationship("ChatParticipant", back_populates="user")
    
    # Video call relationships
    initiated_calls = relationship("VideoCall", foreign_keys="VideoCall.caller_id", back_populates="caller")
    received_calls = relationship("VideoCall", foreign_keys="VideoCall.callee_id", back_populates="callee")
    call_participations = relationship("CallParticipant", back_populates="user")
    
    # Push notification relationships
    device_tokens = relationship("DeviceToken", back_populates="user")
    push_notifications = relationship("PushNotification", back_populates="user")
    
    # Location relationships
    locations = relationship("UserLocation", back_populates="user")
    geofences = relationship("GeofenceArea", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
