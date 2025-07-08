from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.services.chat_service import ChatService
from app.api.v1.auth import get_current_user
from app.schemas.chat import (
    ChatCreate, ChatUpdate, ChatResponse, ChatDetailResponse,
    MessageCreate, MessageUpdate, MessageResponse, MessageListResponse,
    ChatListResponse, ChatParticipantAdd, ChatParticipantUpdate
)
from app.models.user import User
from app.websocket.websocket_handler import broadcast_new_message, broadcast_message_update, broadcast_message_delete
import uuid

router = APIRouter(prefix="/chats", tags=["chats"])


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    """
    Dependency to get chat service instance.
    
    Args:
        db (Session): Database session
        
    Returns:
        ChatService: Chat service instance
    """
    return ChatService(db)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Create a new chat.
    
    Args:
        chat_data (ChatCreate): Chat creation data
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        ChatResponse: Created chat information
    """
    return chat_service.create_chat(chat_data, current_user.id)


@router.get("", response_model=ChatListResponse)
async def get_user_chats(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get all chats for the current user.
    
    Args:
        limit (int): Maximum number of chats to return
        offset (int): Number of chats to skip
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        ChatListResponse: List of user's chats
    """
    return chat_service.get_user_chats(current_user.id, limit, offset)


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat_details(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get detailed chat information including participants.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        ChatDetailResponse: Detailed chat information
    """
    return chat_service.get_chat_details(chat_id, current_user.id)


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    chat_data: ChatUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update chat information.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        chat_data (ChatUpdate): Updated chat data
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        ChatResponse: Updated chat information
    """
    return chat_service.update_chat(chat_id, chat_data, current_user.id)


@router.post("/{chat_id}/participants")
async def add_chat_participants(
    chat_id: uuid.UUID,
    participant_data: ChatParticipantAdd,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Add participants to a chat.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        participant_data (ChatParticipantAdd): Participants to add
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        dict: Success message
    """
    success = chat_service.add_participants(chat_id, participant_data, current_user.id)
    if success:
        return {"message": "Participants added successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add participants"
        )


@router.delete("/{chat_id}/participants/{user_id}")
async def remove_chat_participant(
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Remove a participant from a chat.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        user_id (uuid.UUID): User ID to remove
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        dict: Success message
    """
    success = chat_service.remove_participant(chat_id, user_id, current_user.id)
    if success:
        return {"message": "Participant removed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove participant"
        )


@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: uuid.UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to a chat.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        message_data (MessageCreate): Message data
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        MessageResponse: Sent message information
    """
    message_response = chat_service.send_message(chat_id, message_data, current_user.id)
    
    # Broadcast the new message to other users in the chat
    await broadcast_new_message(message_response.dict(), chat_id, current_user.id)
    
    return message_response


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_message_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get messages from a chat with pagination.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        limit (int): Maximum number of messages to return
        offset (int): Number of messages to skip
        before_message_id (Optional[uuid.UUID]): Get messages before this message ID
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        MessageListResponse: Paginated list of messages
    """
    return chat_service.get_chat_messages(chat_id, current_user.id, limit, offset, before_message_id)


@router.put("/{chat_id}/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    message_data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update a message.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        message_id (uuid.UUID): Message's unique identifier
        message_data (MessageUpdate): Updated message data
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        MessageResponse: Updated message information
    """
    message_response = chat_service.update_message(message_id, message_data, current_user.id)
    
    # Broadcast the message update to other users in the chat
    await broadcast_message_update(message_response.dict(), chat_id)
    
    return message_response


@router.delete("/{chat_id}/messages/{message_id}")
async def delete_message(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a message.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        message_id (uuid.UUID): Message's unique identifier
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        dict: Success message
    """
    success = chat_service.delete_message(message_id, current_user.id)
    
    if success:
        # Broadcast the message deletion to other users in the chat
        await broadcast_message_delete(message_id, chat_id)
        return {"message": "Message deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete message"
        )


@router.post("/{chat_id}/messages/mark-read")
async def mark_messages_as_read(
    chat_id: uuid.UUID,
    up_to_message_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Mark messages as read.
    
    Args:
        chat_id (uuid.UUID): Chat's unique identifier
        up_to_message_id (Optional[uuid.UUID]): Mark messages up to this message ID
        current_user (User): Current authenticated user
        chat_service (ChatService): Chat service
        
    Returns:
        dict: Number of messages marked as read
    """
    count = chat_service.mark_messages_as_read(chat_id, current_user.id, up_to_message_id)
    return {"message": f"Marked {count} messages as read"}
