"""
Video call service for handling video call business logic.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.video_call import VideoCall, CallStatus, CallType
from app.models.user import User
from app.repositories.video_call_repository import VideoCallRepository, CallParticipantRepository
from app.schemas.video_call import (
    VideoCallCreate, VideoCallInitiate, VideoCallResponse, VideoCallUpdate,
    VideoCallHistory, AgoraTokenResponse, CallStatistics, CallParticipantCreate
)
from app.utils.agora_service import agora_service
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)


class VideoCallService:
    """Service for video call operations."""

    def __init__(self, db: Session):
        self.db = db
        self.video_call_repo = VideoCallRepository(db)
        self.participant_repo = CallParticipantRepository(db)

    async def initiate_call(
        self,
        caller_id: int,
        call_data: VideoCallInitiate
    ) -> VideoCallResponse:
        """Initiate a new video call."""
        try:
            # Generate unique channel name
            channel_name = agora_service.generate_channel_name(caller_id, call_data.callee_id)
            
            # Generate Agora UID for caller
            caller_uid = agora_service.generate_uid(caller_id)
            
            # Create call record
            call_create_data = VideoCallCreate(
                callee_id=call_data.callee_id,
                call_type=call_data.call_type,
                is_group_call=call_data.is_group_call
            )
            
            db_call = self.video_call_repo.create_call(
                call_create_data, caller_id, channel_name
            )
            
            # Generate Agora RTC token
            token, expires_at = agora_service.generate_rtc_token(
                channel_name, caller_uid, role=1  # Publisher role
            )
            
            # Update call with Agora details
            update_data = VideoCallUpdate(
                app_id=agora_service.app_id,
                token=token,
                uid=caller_uid
            )
            db_call = self.video_call_repo.update_call(db_call.id, update_data)
            
            # Set status to ringing
            self.video_call_repo.update_call(
                db_call.id, 
                VideoCallUpdate(status=CallStatus.RINGING)
            )
            
            logger.info(f"Call initiated: {db_call.id} from {caller_id} to {call_data.callee_id}")
            
            return VideoCallResponse.from_orm(db_call)
            
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            raise

    async def answer_call(self, call_id: int, user_id: int, accept: bool = True) -> VideoCallResponse:
        """Answer or decline a video call."""
        try:
            db_call = self.video_call_repo.get_call_by_id(call_id)
            if not db_call:
                raise ValueError("Call not found")
            
            # Verify user is the callee
            if db_call.callee_id != user_id:
                raise ValueError("User not authorized to answer this call")
            
            # Check if call is in correct state
            if db_call.status not in [CallStatus.INITIATED, CallStatus.RINGING]:
                raise ValueError("Call cannot be answered in current state")
            
            if accept:
                # Generate Agora UID and token for callee
                callee_uid = agora_service.generate_uid(user_id)
                token, expires_at = agora_service.generate_rtc_token(
                    db_call.channel_name, callee_uid, role=1  # Publisher role
                )
                
                update_data = VideoCallUpdate(status=CallStatus.ANSWERED)
                db_call = self.video_call_repo.update_call(call_id, update_data)
                
                logger.info(f"Call answered: {call_id} by user {user_id}")
            else:
                update_data = VideoCallUpdate(status=CallStatus.DECLINED)
                db_call = self.video_call_repo.update_call(call_id, update_data)
                
                logger.info(f"Call declined: {call_id} by user {user_id}")
            
            return VideoCallResponse.from_orm(db_call)
            
        except Exception as e:
            logger.error(f"Error answering call: {str(e)}")
            raise

    async def end_call(
        self,
        call_id: int,
        user_id: int,
        end_reason: str = None,
        quality_rating: int = None
    ) -> VideoCallResponse:
        """End a video call."""
        try:
            db_call = self.video_call_repo.get_call_by_id(call_id)
            if not db_call:
                raise ValueError("Call not found")
            
            # Verify user is participant in the call
            if user_id not in [db_call.caller_id, db_call.callee_id]:
                raise ValueError("User not authorized to end this call")
            
            # End the call
            db_call = self.video_call_repo.end_call(
                call_id, end_reason, quality_rating
            )
            
            logger.info(f"Call ended: {call_id} by user {user_id}")
            
            return VideoCallResponse.from_orm(db_call)
            
        except Exception as e:
            logger.error(f"Error ending call: {str(e)}")
            raise

    async def get_call(self, call_id: int, user_id: int) -> Optional[VideoCallResponse]:
        """Get call details."""
        db_call = self.video_call_repo.get_call_by_id(call_id)
        if not db_call:
            return None
        
        # Verify user is participant in the call
        if user_id not in [db_call.caller_id, db_call.callee_id]:
            raise ValueError("User not authorized to view this call")
        
        return VideoCallResponse.from_orm(db_call)

    async def get_user_call_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[VideoCallHistory]:
        """Get call history for a user."""
        calls = self.video_call_repo.get_user_calls(user_id, limit, offset)
        return [VideoCallHistory.from_orm(call) for call in calls]

    async def get_active_calls(self, user_id: int) -> List[VideoCallResponse]:
        """Get active calls for a user."""
        calls = self.video_call_repo.get_active_calls_for_user(user_id)
        return [VideoCallResponse.from_orm(call) for call in calls]

    async def generate_agora_token(
        self,
        channel_name: str,
        user_id: int,
        role: int = 1
    ) -> AgoraTokenResponse:
        """Generate a new Agora token for a call."""
        try:
            uid = agora_service.generate_uid(user_id)
            token, expires_at = agora_service.generate_rtc_token(
                channel_name, uid, role
            )
            
            return AgoraTokenResponse(
                token=token,
                channel_name=channel_name,
                uid=uid,
                app_id=agora_service.app_id,
                expires_at=expires_at
            )
            
        except Exception as e:
            logger.error(f"Error generating Agora token: {str(e)}")
            raise

    async def get_call_statistics(self, user_id: int, days: int = 30) -> CallStatistics:
        """Get call statistics for a user."""
        stats = self.video_call_repo.get_call_statistics(user_id, days)
        return CallStatistics(**stats)

    async def add_participant_to_group_call(
        self,
        call_id: int,
        user_id: int,
        participant_user_id: int
    ) -> bool:
        """Add a participant to a group call."""
        try:
            db_call = self.video_call_repo.get_call_by_id(call_id)
            if not db_call:
                raise ValueError("Call not found")
            
            if not db_call.is_group_call:
                raise ValueError("Call is not a group call")
            
            # Verify user is authorized to add participants
            if user_id not in [db_call.caller_id, db_call.callee_id]:
                raise ValueError("User not authorized to add participants")
            
            # Add participant
            participant_data = CallParticipantCreate(user_id=participant_user_id)
            self.participant_repo.add_participant(call_id, participant_data)
            
            logger.info(f"Participant {participant_user_id} added to call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding participant to call: {str(e)}")
            raise

    async def remove_participant_from_group_call(
        self,
        call_id: int,
        user_id: int,
        participant_user_id: int
    ) -> bool:
        """Remove a participant from a group call."""
        try:
            db_call = self.video_call_repo.get_call_by_id(call_id)
            if not db_call:
                raise ValueError("Call not found")
            
            if not db_call.is_group_call:
                raise ValueError("Call is not a group call")
            
            # Verify user is authorized to remove participants
            if user_id not in [db_call.caller_id, db_call.callee_id]:
                raise ValueError("User not authorized to remove participants")
            
            # Remove participant
            success = self.participant_repo.remove_participant(call_id, participant_user_id)
            
            if success:
                logger.info(f"Participant {participant_user_id} removed from call {call_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing participant from call: {str(e)}")
            raise
