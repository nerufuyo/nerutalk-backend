"""
Video call API endpoints for the NeruTalk application.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.video_call_service import VideoCallService
from app.schemas.video_call import (
    VideoCallInitiate, VideoCallResponse, VideoCallAnswer, VideoCallEnd,
    VideoCallHistory, AgoraTokenRequest, AgoraTokenResponse, CallStatistics
)
from app.schemas.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video-calls", tags=["video-calls"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


def get_video_call_service(db: Session = Depends(get_db)) -> VideoCallService:
    """Get video call service instance."""
    return VideoCallService(db)


async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    # This would typically involve JWT token validation
    # For now, we'll use a placeholder implementation
    # In production, implement proper JWT validation
    pass


@router.post("/initiate", response_model=VideoCallResponse)
async def initiate_call(
    call_data: VideoCallInitiate,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Initiate a new video call.
    
    Args:
        call_data: Call initiation data
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        VideoCallResponse: Created call details
    """
    try:
        call = await video_call_service.initiate_call(
            caller_id=current_user.id,
            call_data=call_data
        )
        return call
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate call"
        )


@router.put("/{call_id}/answer", response_model=VideoCallResponse)
async def answer_call(
    call_id: int,
    answer_data: VideoCallAnswer,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Answer or decline a video call.
    
    Args:
        call_id: ID of the call to answer
        answer_data: Answer data (accept/decline)
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        VideoCallResponse: Updated call details
    """
    try:
        call = await video_call_service.answer_call(
            call_id=call_id,
            user_id=current_user.id,
            accept=answer_data.accept
        )
        return call
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error answering call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to answer call"
        )


@router.put("/{call_id}/end", response_model=VideoCallResponse)
async def end_call(
    call_id: int,
    end_data: VideoCallEnd,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    End a video call.
    
    Args:
        call_id: ID of the call to end
        end_data: End call data (reason, rating)
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        VideoCallResponse: Updated call details
    """
    try:
        call = await video_call_service.end_call(
            call_id=call_id,
            user_id=current_user.id,
            end_reason=end_data.end_reason,
            quality_rating=end_data.quality_rating
        )
        return call
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error ending call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end call"
        )


@router.get("/{call_id}", response_model=VideoCallResponse)
async def get_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Get call details by ID.
    
    Args:
        call_id: ID of the call
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        VideoCallResponse: Call details
    """
    try:
        call = await video_call_service.get_call(call_id, current_user.id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        return call
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call"
        )


@router.get("/", response_model=List[VideoCallResponse])
async def get_active_calls(
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Get active calls for the current user.
    
    Args:
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        List[VideoCallResponse]: List of active calls
    """
    try:
        calls = await video_call_service.get_active_calls(current_user.id)
        return calls
    except Exception as e:
        logger.error(f"Error getting active calls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active calls"
        )


@router.get("/history/", response_model=List[VideoCallHistory])
async def get_call_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Get call history for the current user.
    
    Args:
        limit: Maximum number of calls to return
        offset: Number of calls to skip
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        List[VideoCallHistory]: List of call history
    """
    try:
        history = await video_call_service.get_user_call_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return history
    except Exception as e:
        logger.error(f"Error getting call history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call history"
        )


@router.post("/token", response_model=AgoraTokenResponse)
async def generate_agora_token(
    token_request: AgoraTokenRequest,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Generate Agora RTC token for video calling.
    
    Args:
        token_request: Token request data
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        AgoraTokenResponse: Generated token details
    """
    try:
        token_response = await video_call_service.generate_agora_token(
            channel_name=token_request.channel_name,
            user_id=current_user.id,
            role=token_request.role
        )
        return token_response
    except Exception as e:
        logger.error(f"Error generating Agora token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate token"
        )


@router.get("/statistics/", response_model=CallStatistics)
async def get_call_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Get call statistics for the current user.
    
    Args:
        days: Number of days to include in statistics
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        CallStatistics: User's call statistics
    """
    try:
        stats = await video_call_service.get_call_statistics(
            user_id=current_user.id,
            days=days
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting call statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call statistics"
        )


@router.put("/{call_id}/participants/{user_id}/add")
async def add_participant_to_group_call(
    call_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Add a participant to a group call.
    
    Args:
        call_id: ID of the call
        user_id: ID of the user to add
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        Success message
    """
    try:
        success = await video_call_service.add_participant_to_group_call(
            call_id=call_id,
            user_id=current_user.id,
            participant_user_id=user_id
        )
        if success:
            return {"message": "Participant added successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add participant"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding participant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add participant"
        )


@router.put("/{call_id}/participants/{user_id}/remove")
async def remove_participant_from_group_call(
    call_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    video_call_service: VideoCallService = Depends(get_video_call_service)
):
    """
    Remove a participant from a group call.
    
    Args:
        call_id: ID of the call
        user_id: ID of the user to remove
        current_user: Current authenticated user
        video_call_service: Video call service instance
        
    Returns:
        Success message
    """
    try:
        success = await video_call_service.remove_participant_from_group_call(
            call_id=call_id,
            user_id=current_user.id,
            participant_user_id=user_id
        )
        if success:
            return {"message": "Participant removed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove participant"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing participant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove participant"
        )
