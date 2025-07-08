from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from app.models.chat import Chat, ChatType
from app.models.message import Message, MessageType, MessageStatus
from app.models.chat_participant import ChatParticipant, ParticipantRole
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatUpdate, MessageCreate, MessageUpdate
import uuid


class ChatRepository:
    """
    Repository class for Chat database operations.
    
    This class encapsulates all database operations related to chats,
    providing a clean interface for the service layer.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
    
    def create_chat(self, chat_data: ChatCreate, creator_id: uuid.UUID) -> Chat:
        """
        Create a new chat.
        
        Args:
            chat_data (ChatCreate): Chat creation data
            creator_id (uuid.UUID): ID of user creating the chat
            
        Returns:
            Chat: Created chat instance
        """
        db_chat = Chat(
            name=chat_data.name,
            description=chat_data.description,
            chat_type=chat_data.chat_type,
            created_by=creator_id
        )
        
        self.db.add(db_chat)
        self.db.flush()  # Flush to get the chat ID
        
        # Add creator as owner
        creator_participant = ChatParticipant(
            user_id=creator_id,
            chat_id=db_chat.id,
            role=ParticipantRole.OWNER
        )
        self.db.add(creator_participant)
        
        # Add other participants
        for participant_id in chat_data.participant_ids:
            if participant_id != creator_id:  # Don't add creator twice
                participant = ChatParticipant(
                    user_id=participant_id,
                    chat_id=db_chat.id,
                    role=ParticipantRole.MEMBER
                )
                self.db.add(participant)
        
        self.db.commit()
        self.db.refresh(db_chat)
        return db_chat
    
    def get_chat_by_id(self, chat_id: uuid.UUID) -> Optional[Chat]:
        """
        Get a chat by its ID.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            
        Returns:
            Optional[Chat]: Chat instance or None if not found
        """
        return self.db.query(Chat).filter(Chat.id == chat_id).first()
    
    def get_chat_with_participants(self, chat_id: uuid.UUID) -> Optional[Chat]:
        """
        Get a chat with its participants loaded.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            
        Returns:
            Optional[Chat]: Chat instance with participants or None if not found
        """
        return self.db.query(Chat).options(
            joinedload(Chat.participants).joinedload(ChatParticipant.user)
        ).filter(Chat.id == chat_id).first()
    
    def get_user_chats(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[Chat]:
        """
        Get all chats for a user.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            limit (int): Maximum number of chats to return
            offset (int): Number of chats to skip
            
        Returns:
            List[Chat]: List of user's chats
        """
        return self.db.query(Chat).join(ChatParticipant).filter(
            and_(
                ChatParticipant.user_id == user_id,
                ChatParticipant.is_active == True,
                Chat.is_active == True
            )
        ).order_by(desc(Chat.updated_at)).limit(limit).offset(offset).all()
    
    def get_private_chat(self, user1_id: uuid.UUID, user2_id: uuid.UUID) -> Optional[Chat]:
        """
        Get existing private chat between two users.
        
        Args:
            user1_id (uuid.UUID): First user's ID
            user2_id (uuid.UUID): Second user's ID
            
        Returns:
            Optional[Chat]: Private chat instance or None if not found
        """
        # Subquery to get chats with both users
        chat_ids = self.db.query(ChatParticipant.chat_id).filter(
            ChatParticipant.user_id.in_([user1_id, user2_id])
        ).group_by(ChatParticipant.chat_id).having(
            func.count(ChatParticipant.user_id) == 2
        ).subquery()
        
        return self.db.query(Chat).filter(
            and_(
                Chat.id.in_(chat_ids),
                Chat.chat_type == ChatType.PRIVATE,
                Chat.is_active == True
            )
        ).first()
    
    def update_chat(self, chat_id: uuid.UUID, chat_data: ChatUpdate) -> Optional[Chat]:
        """
        Update chat information.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            chat_data (ChatUpdate): Updated chat data
            
        Returns:
            Optional[Chat]: Updated chat instance or None if not found
        """
        db_chat = self.get_chat_by_id(chat_id)
        if not db_chat:
            return None
        
        update_data = chat_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_chat, field, value)
        
        self.db.commit()
        self.db.refresh(db_chat)
        return db_chat
    
    def add_participants(self, chat_id: uuid.UUID, user_ids: List[uuid.UUID]) -> bool:
        """
        Add participants to a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_ids (List[uuid.UUID]): List of user IDs to add
            
        Returns:
            bool: True if participants added successfully
        """
        # Check if users are already participants
        existing_participants = self.db.query(ChatParticipant.user_id).filter(
            and_(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id.in_(user_ids),
                ChatParticipant.is_active == True
            )
        ).all()
        
        existing_user_ids = {p.user_id for p in existing_participants}
        new_user_ids = [uid for uid in user_ids if uid not in existing_user_ids]
        
        for user_id in new_user_ids:
            participant = ChatParticipant(
                user_id=user_id,
                chat_id=chat_id,
                role=ParticipantRole.MEMBER
            )
            self.db.add(participant)
        
        if new_user_ids:
            self.db.commit()
        
        return True
    
    def remove_participant(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Remove a participant from a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User ID to remove
            
        Returns:
            bool: True if participant removed successfully
        """
        participant = self.db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.is_active == True
            )
        ).first()
        
        if participant:
            participant.is_active = False
            participant.left_at = func.now()
            self.db.commit()
            return True
        
        return False
    
    def update_participant_role(self, chat_id: uuid.UUID, user_id: uuid.UUID, 
                               role: ParticipantRole) -> bool:
        """
        Update participant's role in a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User ID to update
            role (ParticipantRole): New role
            
        Returns:
            bool: True if role updated successfully
        """
        participant = self.db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.is_active == True
            )
        ).first()
        
        if participant:
            participant.role = role
            self.db.commit()
            return True
        
        return False
    
    def is_user_participant(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Check if user is a participant in the chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            bool: True if user is a participant
        """
        participant = self.db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.is_active == True
            )
        ).first()
        
        return participant is not None
    
    def get_participant_role(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ParticipantRole]:
        """
        Get user's role in a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            Optional[ParticipantRole]: User's role or None if not a participant
        """
        participant = self.db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.is_active == True
            )
        ).first()
        
        return participant.role if participant else None
