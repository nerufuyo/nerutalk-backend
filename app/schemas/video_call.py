"""
Video call schemas for request/response data validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.video_call import CallType, CallStatus


class CallParticipantBase(BaseModel):
    """Base schema for call participants."""
    user_id: int
    is_muted: bool = False
    is_video_enabled: bool = True


class CallParticipantCreate(CallParticipantBase):
    """Schema for creating a call participant."""
    pass


class CallParticipantUpdate(BaseModel):
    """Schema for updating call participant."""
    is_muted: Optional[bool] = None
    is_video_enabled: Optional[bool] = None


class CallParticipantResponse(CallParticipantBase):
    """Schema for call participant response."""
    id: int
    call_id: int
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    agora_uid: Optional[int] = None

    class Config:
        from_attributes = True


class VideoCallBase(BaseModel):
    """Base schema for video calls."""
    call_type: CallType = CallType.VIDEO
    is_group_call: bool = False


class VideoCallCreate(VideoCallBase):
    """Schema for creating a video call."""
    callee_id: int


class VideoCallInitiate(BaseModel):
    """Schema for initiating a video call."""
    callee_id: int
    call_type: CallType = CallType.VIDEO
    is_group_call: bool = False


class VideoCallAnswer(BaseModel):
    """Schema for answering a video call."""
    accept: bool = True


class VideoCallEnd(BaseModel):
    """Schema for ending a video call."""
    end_reason: Optional[str] = None
    quality_rating: Optional[int] = Field(None, ge=1, le=5)


class VideoCallUpdate(BaseModel):
    """Schema for updating a video call."""
    status: Optional[CallStatus] = None
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    end_reason: Optional[str] = None


class VideoCallResponse(VideoCallBase):
    """Schema for video call response."""
    id: int
    channel_name: str
    status: CallStatus
    caller_id: int
    callee_id: int
    app_id: Optional[str] = None
    token: Optional[str] = None
    uid: Optional[int] = None
    initiated_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    quality_rating: Optional[int] = None
    end_reason: Optional[str] = None
    participants: List[CallParticipantResponse] = []

    class Config:
        from_attributes = True


class VideoCallHistory(BaseModel):
    """Schema for call history."""
    id: int
    call_type: CallType
    status: CallStatus
    caller_id: int
    callee_id: int
    initiated_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    quality_rating: Optional[int] = None

    class Config:
        from_attributes = True


class AgoraTokenRequest(BaseModel):
    """Schema for requesting Agora token."""
    channel_name: str
    uid: int
    role: int = 1  # 1 for publisher, 2 for subscriber


class AgoraTokenResponse(BaseModel):
    """Schema for Agora token response."""
    token: str
    channel_name: str
    uid: int
    app_id: str
    expires_at: datetime


class CallStatistics(BaseModel):
    """Schema for call statistics."""
    total_calls: int
    total_video_calls: int
    total_audio_calls: int
    total_duration: int  # in seconds
    average_duration: float  # in seconds
    successful_calls: int
    missed_calls: int
    declined_calls: int
