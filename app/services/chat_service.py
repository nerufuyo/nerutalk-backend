from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import (
    ChatCreate, ChatUpdate, ChatResponse, ChatDetailResponse,
    MessageCreate, MessageUpdate, MessageResponse, MessageListResponse,
    ChatListResponse, ChatParticipantAdd, ChatParticipantUpdate,
    ParticipantRole, ChatType
)
from app.models.chat import Chat
from app.models.message import Message, MessageType, MessageStatus
from app.models.chat_participant import ChatParticipant
import uuid


class ChatService:
    """
    Service class for chat and messaging operations.
    
    This class contains the business logic for chat management,
    messaging, and real-time communication features.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the service with a database session.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.message_repo = MessageRepository(db)
        self.user_repo = UserRepository(db)
    
    def create_chat(self, chat_data: ChatCreate, creator_id: uuid.UUID) -> ChatResponse:
        """
        Create a new chat.
        
        Args:
            chat_data (ChatCreate): Chat creation data
            creator_id (uuid.UUID): ID of user creating the chat
            
        Returns:
            ChatResponse: Created chat data
            
        Raises:
            HTTPException: If validation fails or participants not found
        """
        # Validate that all participant users exist
        for user_id in chat_data.participant_ids:
            user = self.user_repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with ID {user_id} not found or inactive"
                )
        
        # For private chats, check if chat already exists
        if chat_data.chat_type == ChatType.PRIVATE:
            if len(chat_data.participant_ids) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Private chat must have exactly one other participant"
                )
            
            other_user_id = chat_data.participant_ids[0]
            existing_chat = self.chat_repo.get_private_chat(creator_id, other_user_id)
            if existing_chat:
                return self._build_chat_response(existing_chat, creator_id)
        
        # Create the chat
        db_chat = self.chat_repo.create_chat(chat_data, creator_id)
        return self._build_chat_response(db_chat, creator_id)
    
    def get_user_chats(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> ChatListResponse:
        """
        Get all chats for a user.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            limit (int): Maximum number of chats to return
            offset (int): Number of chats to skip
            
        Returns:
            ChatListResponse: List of user's chats
        """
        chats = self.chat_repo.get_user_chats(user_id, limit, offset)
        chat_responses = [self._build_chat_response(chat, user_id) for chat in chats]
        
        return ChatListResponse(
            chats=chat_responses,
            total_count=len(chat_responses)
        )
    
    def get_chat_details(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> ChatDetailResponse:
        """
        Get detailed chat information including participants.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): Requesting user's ID
            
        Returns:
            ChatDetailResponse: Detailed chat information
            
        Raises:
            HTTPException: If chat not found or user not authorized
        """
        # Check if user is a participant
        if not self.chat_repo.is_user_participant(chat_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this chat"
            )
        
        chat = self.chat_repo.get_chat_with_participants(chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        return self._build_chat_detail_response(chat, user_id)
    
    def update_chat(self, chat_id: uuid.UUID, chat_data: ChatUpdate, user_id: uuid.UUID) -> ChatResponse:
        """
        Update chat information.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            chat_data (ChatUpdate): Updated chat data
            user_id (uuid.UUID): User updating the chat
            
        Returns:
            ChatResponse: Updated chat data
            
        Raises:
            HTTPException: If chat not found or user not authorized
        """
        # Check if user has admin privileges
        user_role = self.chat_repo.get_participant_role(chat_id, user_id)
        if not user_role or user_role not in [ParticipantRole.ADMIN, ParticipantRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this chat"
            )
        
        updated_chat = self.chat_repo.update_chat(chat_id, chat_data)
        if not updated_chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        return self._build_chat_response(updated_chat, user_id)
    
    def add_participants(self, chat_id: uuid.UUID, participant_data: ChatParticipantAdd,
                        user_id: uuid.UUID) -> bool:
        """
        Add participants to a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            participant_data (ChatParticipantAdd): Participants to add
            user_id (uuid.UUID): User adding participants
            
        Returns:
            bool: True if participants added successfully
            
        Raises:
            HTTPException: If chat not found or user not authorized
        """
        # Check if user has admin privileges
        user_role = self.chat_repo.get_participant_role(chat_id, user_id)
        if not user_role or user_role not in [ParticipantRole.ADMIN, ParticipantRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add participants"
            )
        
        # Check if it's a group chat (can't add to private chats)
        chat = self.chat_repo.get_chat_by_id(chat_id)
        if not chat or chat.chat_type == ChatType.PRIVATE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add participants to private chats"
            )
        
        # Validate that all users exist
        for participant_id in participant_data.user_ids:
            user = self.user_repo.get_user_by_id(participant_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with ID {participant_id} not found or inactive"
                )
        
        return self.chat_repo.add_participants(chat_id, participant_data.user_ids)
    
    def remove_participant(self, chat_id: uuid.UUID, participant_id: uuid.UUID,
                          user_id: uuid.UUID) -> bool:
        """
        Remove a participant from a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            participant_id (uuid.UUID): ID of participant to remove
            user_id (uuid.UUID): User removing the participant
            
        Returns:
            bool: True if participant removed successfully
            
        Raises:
            HTTPException: If not authorized or invalid operation
        """
        user_role = self.chat_repo.get_participant_role(chat_id, user_id)
        participant_role = self.chat_repo.get_participant_role(chat_id, participant_id)
        
        # Check permissions
        if user_id == participant_id:
            # Users can always leave a chat themselves
            pass
        elif user_role in [ParticipantRole.ADMIN, ParticipantRole.OWNER]:
            # Admins can remove members, owners can remove anyone except other owners
            if participant_role == ParticipantRole.OWNER and user_role != ParticipantRole.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot remove chat owner"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove participants"
            )
        
        return self.chat_repo.remove_participant(chat_id, participant_id)
    
    def send_message(self, chat_id: uuid.UUID, message_data: MessageCreate,
                    sender_id: uuid.UUID) -> MessageResponse:
        """
        Send a message to a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            message_data (MessageCreate): Message data
            sender_id (uuid.UUID): ID of user sending the message
            
        Returns:
            MessageResponse: Sent message data
            
        Raises:
            HTTPException: If chat not found or user not authorized
        """
        # Check if user is a participant
        if not self.chat_repo.is_user_participant(chat_id, sender_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this chat"
            )
        
        # Validate reply_to message if provided
        if message_data.reply_to_id:
            reply_message = self.message_repo.get_message_by_id(message_data.reply_to_id)
            if not reply_message or reply_message.chat_id != chat_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reply message"
                )
        
        # Create the message
        db_message = self.message_repo.create_message(message_data, sender_id, chat_id)
        return self._build_message_response(db_message)
    
    def get_chat_messages(self, chat_id: uuid.UUID, user_id: uuid.UUID,
                         limit: int = 50, offset: int = 0,
                         before_message_id: Optional[uuid.UUID] = None) -> MessageListResponse:
        """
        Get messages from a chat with pagination.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): Requesting user's ID
            limit (int): Maximum number of messages to return
            offset (int): Number of messages to skip
            before_message_id (Optional[uuid.UUID]): Get messages before this message ID
            
        Returns:
            MessageListResponse: Paginated list of messages
            
        Raises:
            HTTPException: If chat not found or user not authorized
        """
        # Check if user is a participant
        if not self.chat_repo.is_user_participant(chat_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this chat"
            )
        
        messages = self.message_repo.get_chat_messages(chat_id, limit, offset, before_message_id)
        message_responses = [self._build_message_response(msg) for msg in messages]
        
        return MessageListResponse(
            messages=message_responses,
            total_count=len(message_responses),
            page=offset // limit + 1 if limit > 0 else 1,
            page_size=limit,
            has_next=len(messages) == limit,
            has_prev=offset > 0
        )
    
    def update_message(self, message_id: uuid.UUID, message_data: MessageUpdate,
                      user_id: uuid.UUID) -> MessageResponse:
        """
        Update a message.
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            message_data (MessageUpdate): Updated message data
            user_id (uuid.UUID): User updating the message
            
        Returns:
            MessageResponse: Updated message data
            
        Raises:
            HTTPException: If message not found or user not authorized
        """
        updated_message = self.message_repo.update_message(message_id, message_data, user_id)
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or you don't have permission to edit it"
            )
        
        return self._build_message_response(updated_message)
    
    def delete_message(self, message_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete a message.
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            user_id (uuid.UUID): User deleting the message
            
        Returns:
            bool: True if message deleted successfully
            
        Raises:
            HTTPException: If message not found or user not authorized
        """
        success = self.message_repo.delete_message(message_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or you don't have permission to delete it"
            )
        
        return True
    
    def mark_messages_as_read(self, chat_id: uuid.UUID, user_id: uuid.UUID,
                             up_to_message_id: Optional[uuid.UUID] = None) -> int:
        """
        Mark messages as read.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User marking messages as read
            up_to_message_id (Optional[uuid.UUID]): Mark messages up to this message ID
            
        Returns:
            int: Number of messages marked as read
            
        Raises:
            HTTPException: If chat not found or user not authorized
        """
        # Check if user is a participant
        if not self.chat_repo.is_user_participant(chat_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this chat"
            )
        
        return self.message_repo.mark_messages_as_read(chat_id, user_id, up_to_message_id)
    
    def _build_chat_response(self, chat: Chat, user_id: uuid.UUID) -> ChatResponse:
        """Build ChatResponse from Chat model."""
        # Get unread count for this user
        unread_count = self.message_repo.get_unread_message_count(chat.id, user_id)
        
        # Get last message info
        last_messages = self.message_repo.get_chat_messages(chat.id, limit=1)
        last_message = None
        last_message_at = None
        if last_messages:
            last_message = last_messages[0].content
            last_message_at = last_messages[0].created_at
        
        return ChatResponse(
            id=chat.id,
            name=chat.name,
            description=chat.description,
            chat_type=chat.chat_type,
            avatar_url=chat.avatar_url,
            is_active=chat.is_active,
            created_by=chat.created_by,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            participant_count=len([p for p in chat.participants if p.is_active]),
            last_message=last_message,
            last_message_at=last_message_at,
            unread_count=unread_count
        )
    
    def _build_chat_detail_response(self, chat: Chat, user_id: uuid.UUID) -> ChatDetailResponse:
        """Build ChatDetailResponse from Chat model with participants."""
        base_response = self._build_chat_response(chat, user_id)
        
        # Build participant responses
        participants = []
        for participant in chat.participants:
            if participant.is_active:
                participants.append({
                    "id": participant.id,
                    "user_id": participant.user_id,
                    "role": participant.role,
                    "is_muted": participant.is_muted,
                    "is_pinned": participant.is_pinned,
                    "joined_at": participant.joined_at,
                    "username": participant.user.username,
                    "full_name": participant.user.full_name,
                    "avatar_url": participant.user.avatar_url,
                    "is_online": participant.user.is_online
                })
        
        return ChatDetailResponse(
            **base_response.dict(),
            participants=participants
        )
    
    def _build_message_response(self, message: Message) -> MessageResponse:
        """Build MessageResponse from Message model."""
        # Get reply info if applicable
        reply_to_content = None
        reply_to_sender = None
        if message.reply_to:
            reply_to_content = message.reply_to.content
            reply_to_sender = message.reply_to.sender.username
        
        return MessageResponse(
            id=message.id,
            content=message.content,
            message_type=message.message_type,
            status=message.status,
            file_url=message.file_url,
            file_name=message.file_name,
            file_size=message.file_size,
            thumbnail_url=message.thumbnail_url,
            metadata=message.metadata,
            reply_to_id=message.reply_to_id,
            is_edited=message.is_edited,
            is_deleted=message.is_deleted,
            sender_id=message.sender_id,
            chat_id=message.chat_id,
            created_at=message.created_at,
            updated_at=message.updated_at,
            delivered_at=message.delivered_at,
            read_at=message.read_at,
            sender_username=message.sender.username,
            sender_full_name=message.sender.full_name,
            sender_avatar_url=message.sender.avatar_url,
            reply_to_content=reply_to_content,
            reply_to_sender=reply_to_sender
        )
