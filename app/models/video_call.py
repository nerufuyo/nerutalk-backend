"""
Video call models for the NeruTalk application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from app.core.database import Base


class CallType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"


class CallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    DECLINED = "declined"
    ENDED = "ended"
    MISSED = "missed"
    FAILED = "failed"


class VideoCall(Base):
    """Video/Audio call model."""
    __tablename__ = "video_calls"

    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String, unique=True, index=True, nullable=False)
    call_type = Column(SQLEnum(CallType), nullable=False, default=CallType.VIDEO)
    status = Column(SQLEnum(CallStatus), nullable=False, default=CallStatus.INITIATED)
    
    # Participants
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    callee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Agora specific
    app_id = Column(String, nullable=True)
    token = Column(String, nullable=True)
    uid = Column(Integer, nullable=True)
    
    # Call timing
    initiated_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True, default=0)  # in seconds
    
    # Additional info
    is_group_call = Column(Boolean, default=False)
    quality_rating = Column(Integer, nullable=True)  # 1-5 rating
    end_reason = Column(String, nullable=True)
    
    # Relationships
    caller = relationship("User", foreign_keys=[caller_id], back_populates="initiated_calls")
    callee = relationship("User", foreign_keys=[callee_id], back_populates="received_calls")
    participants = relationship("CallParticipant", back_populates="call")


class CallParticipant(Base):
    """Call participant model for group calls."""
    __tablename__ = "call_participants"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("video_calls.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Participant specific
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    is_muted = Column(Boolean, default=False)
    is_video_enabled = Column(Boolean, default=True)
    agora_uid = Column(Integer, nullable=True)
    
    # Relationships
    call = relationship("VideoCall", back_populates="participants")
    user = relationship("User", back_populates="call_participations")
