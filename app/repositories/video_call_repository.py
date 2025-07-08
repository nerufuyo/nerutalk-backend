"""
Video call repository for database operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from app.models.video_call import VideoCall, CallParticipant, CallStatus, CallType
from app.models.user import User
from app.schemas.video_call import VideoCallCreate, VideoCallUpdate, CallParticipantCreate


class VideoCallRepository:
    """Repository for video call operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_call(self, call_data: VideoCallCreate, caller_id: int, channel_name: str) -> VideoCall:
        """Create a new video call."""
        db_call = VideoCall(
            channel_name=channel_name,
            call_type=call_data.call_type,
            caller_id=caller_id,
            callee_id=call_data.callee_id,
            is_group_call=call_data.is_group_call,
            initiated_at=datetime.utcnow()
        )
        self.db.add(db_call)
        self.db.commit()
        self.db.refresh(db_call)
        return db_call

    def get_call_by_id(self, call_id: int) -> Optional[VideoCall]:
        """Get a call by ID."""
        return self.db.query(VideoCall).filter(VideoCall.id == call_id).first()

    def get_call_by_channel(self, channel_name: str) -> Optional[VideoCall]:
        """Get a call by channel name."""
        return self.db.query(VideoCall).filter(VideoCall.channel_name == channel_name).first()

    def update_call(self, call_id: int, call_data: VideoCallUpdate) -> Optional[VideoCall]:
        """Update a video call."""
        db_call = self.get_call_by_id(call_id)
        if not db_call:
            return None

        update_data = call_data.dict(exclude_unset=True)
        
        # Handle status updates with timestamps
        if "status" in update_data:
            if update_data["status"] == CallStatus.ANSWERED and not db_call.answered_at:
                update_data["answered_at"] = datetime.utcnow()
            elif update_data["status"] in [CallStatus.ENDED, CallStatus.DECLINED, CallStatus.MISSED]:
                if not db_call.ended_at:
                    update_data["ended_at"] = datetime.utcnow()
                    # Calculate duration if call was answered
                    if db_call.answered_at:
                        duration = (datetime.utcnow() - db_call.answered_at).total_seconds()
                        update_data["duration"] = int(duration)

        for field, value in update_data.items():
            setattr(db_call, field, value)

        self.db.commit()
        self.db.refresh(db_call)
        return db_call

    def end_call(self, call_id: int, end_reason: str = None, quality_rating: int = None) -> Optional[VideoCall]:
        """End a video call."""
        update_data = VideoCallUpdate(
            status=CallStatus.ENDED,
            end_reason=end_reason,
            quality_rating=quality_rating
        )
        return self.update_call(call_id, update_data)

    def get_user_calls(self, user_id: int, limit: int = 50, offset: int = 0) -> List[VideoCall]:
        """Get calls for a user (both as caller and callee)."""
        return (
            self.db.query(VideoCall)
            .filter(
                or_(
                    VideoCall.caller_id == user_id,
                    VideoCall.callee_id == user_id
                )
            )
            .order_by(desc(VideoCall.initiated_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_active_calls_for_user(self, user_id: int) -> List[VideoCall]:
        """Get active calls for a user."""
        return (
            self.db.query(VideoCall)
            .filter(
                and_(
                    or_(
                        VideoCall.caller_id == user_id,
                        VideoCall.callee_id == user_id
                    ),
                    VideoCall.status.in_([
                        CallStatus.INITIATED,
                        CallStatus.RINGING,
                        CallStatus.ANSWERED
                    ])
                )
            )
            .all()
        )

    def get_call_statistics(self, user_id: int, days: int = 30) -> dict:
        """Get call statistics for a user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = (
            self.db.query(
                func.count(VideoCall.id).label("total_calls"),
                func.count(
                    func.case(
                        (VideoCall.call_type == CallType.VIDEO, 1)
                    )
                ).label("total_video_calls"),
                func.count(
                    func.case(
                        (VideoCall.call_type == CallType.AUDIO, 1)
                    )
                ).label("total_audio_calls"),
                func.sum(
                    func.coalesce(VideoCall.duration, 0)
                ).label("total_duration"),
                func.avg(
                    func.coalesce(VideoCall.duration, 0)
                ).label("average_duration"),
                func.count(
                    func.case(
                        (VideoCall.status == CallStatus.ANSWERED, 1)
                    )
                ).label("successful_calls"),
                func.count(
                    func.case(
                        (VideoCall.status == CallStatus.MISSED, 1)
                    )
                ).label("missed_calls"),
                func.count(
                    func.case(
                        (VideoCall.status == CallStatus.DECLINED, 1)
                    )
                ).label("declined_calls"),
            )
            .filter(
                and_(
                    or_(
                        VideoCall.caller_id == user_id,
                        VideoCall.callee_id == user_id
                    ),
                    VideoCall.initiated_at >= start_date
                )
            )
            .first()
        )

        return {
            "total_calls": stats.total_calls or 0,
            "total_video_calls": stats.total_video_calls or 0,
            "total_audio_calls": stats.total_audio_calls or 0,
            "total_duration": int(stats.total_duration or 0),
            "average_duration": float(stats.average_duration or 0),
            "successful_calls": stats.successful_calls or 0,
            "missed_calls": stats.missed_calls or 0,
            "declined_calls": stats.declined_calls or 0,
        }

    def delete_call(self, call_id: int) -> bool:
        """Delete a video call."""
        db_call = self.get_call_by_id(call_id)
        if not db_call:
            return False

        self.db.delete(db_call)
        self.db.commit()
        return True


class CallParticipantRepository:
    """Repository for call participant operations."""

    def __init__(self, db: Session):
        self.db = db

    def add_participant(self, call_id: int, participant_data: CallParticipantCreate) -> CallParticipant:
        """Add a participant to a call."""
        db_participant = CallParticipant(
            call_id=call_id,
            user_id=participant_data.user_id,
            is_muted=participant_data.is_muted,
            is_video_enabled=participant_data.is_video_enabled,
            joined_at=datetime.utcnow()
        )
        self.db.add(db_participant)
        self.db.commit()
        self.db.refresh(db_participant)
        return db_participant

    def get_call_participants(self, call_id: int) -> List[CallParticipant]:
        """Get all participants for a call."""
        return (
            self.db.query(CallParticipant)
            .filter(CallParticipant.call_id == call_id)
            .all()
        )

    def update_participant(self, participant_id: int, **kwargs) -> Optional[CallParticipant]:
        """Update a call participant."""
        db_participant = (
            self.db.query(CallParticipant)
            .filter(CallParticipant.id == participant_id)
            .first()
        )
        if not db_participant:
            return None

        for field, value in kwargs.items():
            if hasattr(db_participant, field):
                setattr(db_participant, field, value)

        self.db.commit()
        self.db.refresh(db_participant)
        return db_participant

    def remove_participant(self, call_id: int, user_id: int) -> bool:
        """Remove a participant from a call."""
        db_participant = (
            self.db.query(CallParticipant)
            .filter(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id
                )
            )
            .first()
        )
        if not db_participant:
            return False

        db_participant.left_at = datetime.utcnow()
        self.db.commit()
        return True
