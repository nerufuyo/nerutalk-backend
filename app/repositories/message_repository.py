from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from app.models.message import Message, MessageType, MessageStatus
from app.models.chat_participant import ChatParticipant
from app.models.user import User
from app.schemas.chat import MessageCreate, MessageUpdate
from datetime import datetime
import uuid


class MessageRepository:
    """
    Repository class for Message database operations.
    
    This class encapsulates all database operations related to messages,
    providing a clean interface for the service layer.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
    
    def create_message(self, message_data: MessageCreate, sender_id: uuid.UUID, 
                      chat_id: uuid.UUID) -> Message:
        """
        Create a new message.
        
        Args:
            message_data (MessageCreate): Message creation data
            sender_id (uuid.UUID): ID of user sending the message
            chat_id (uuid.UUID): ID of chat to send message to
            
        Returns:
            Message: Created message instance
        """
        db_message = Message(
            content=message_data.content,
            message_type=message_data.message_type,
            reply_to_id=message_data.reply_to_id,
            metadata=message_data.metadata,
            sender_id=sender_id,
            chat_id=chat_id
        )
        
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message
    
    def get_message_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """
        Get a message by its ID.
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            
        Returns:
            Optional[Message]: Message instance or None if not found
        """
        return self.db.query(Message).filter(
            and_(Message.id == message_id, Message.is_deleted == False)
        ).first()
    
    def get_message_with_details(self, message_id: uuid.UUID) -> Optional[Message]:
        """
        Get a message with sender details loaded.
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            
        Returns:
            Optional[Message]: Message instance with sender details or None if not found
        """
        return self.db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.reply_to).joinedload(Message.sender)
        ).filter(
            and_(Message.id == message_id, Message.is_deleted == False)
        ).first()
    
    def get_chat_messages(self, chat_id: uuid.UUID, limit: int = 50, 
                         offset: int = 0, before_message_id: Optional[uuid.UUID] = None) -> List[Message]:
        """
        Get messages from a chat with pagination.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            limit (int): Maximum number of messages to return
            offset (int): Number of messages to skip
            before_message_id (Optional[uuid.UUID]): Get messages before this message ID
            
        Returns:
            List[Message]: List of messages
        """
        query = self.db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.reply_to).joinedload(Message.sender)
        ).filter(
            and_(
                Message.chat_id == chat_id,
                Message.is_deleted == False
            )
        )
        
        if before_message_id:
            # Get the timestamp of the reference message
            ref_message = self.db.query(Message).filter(
                Message.id == before_message_id
            ).first()
            if ref_message:
                query = query.filter(Message.created_at < ref_message.created_at)
        
        return query.order_by(desc(Message.created_at)).limit(limit).offset(offset).all()
    
    def update_message(self, message_id: uuid.UUID, message_data: MessageUpdate,
                      user_id: uuid.UUID) -> Optional[Message]:
        """
        Update a message (only by the sender).
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            message_data (MessageUpdate): Updated message data
            user_id (uuid.UUID): ID of user updating the message
            
        Returns:
            Optional[Message]: Updated message instance or None if not found or unauthorized
        """
        db_message = self.db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.sender_id == user_id,
                Message.is_deleted == False
            )
        ).first()
        
        if not db_message:
            return None
        
        db_message.content = message_data.content
        db_message.is_edited = True
        
        self.db.commit()
        self.db.refresh(db_message)
        return db_message
    
    def delete_message(self, message_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete a message (soft delete).
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            user_id (uuid.UUID): ID of user deleting the message
            
        Returns:
            bool: True if message deleted successfully
        """
        db_message = self.db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.sender_id == user_id,
                Message.is_deleted == False
            )
        ).first()
        
        if not db_message:
            return False
        
        db_message.is_deleted = True
        self.db.commit()
        return True
    
    def update_message_status(self, message_id: uuid.UUID, status: MessageStatus,
                             timestamp: Optional[datetime] = None) -> bool:
        """
        Update message status (delivered, read).
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            status (MessageStatus): New message status
            timestamp (Optional[datetime]): Status timestamp
            
        Returns:
            bool: True if status updated successfully
        """
        db_message = self.get_message_by_id(message_id)
        if not db_message:
            return False
        
        db_message.status = status
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if status == MessageStatus.DELIVERED:
            db_message.delivered_at = timestamp
        elif status == MessageStatus.READ:
            db_message.read_at = timestamp
            # Also mark as delivered if not already
            if db_message.delivered_at is None:
                db_message.delivered_at = timestamp
        
        self.db.commit()
        return True
    
    def mark_messages_as_read(self, chat_id: uuid.UUID, user_id: uuid.UUID, 
                             up_to_message_id: Optional[uuid.UUID] = None) -> int:
        """
        Mark messages as read by a user.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User marking messages as read
            up_to_message_id (Optional[uuid.UUID]): Mark messages up to this message ID
            
        Returns:
            int: Number of messages marked as read
        """
        query = self.db.query(Message).filter(
            and_(
                Message.chat_id == chat_id,
                Message.sender_id != user_id,  # Don't mark own messages as read
                Message.is_deleted == False,
                or_(
                    Message.status == MessageStatus.SENT,
                    Message.status == MessageStatus.DELIVERED
                )
            )
        )
        
        if up_to_message_id:
            # Get the timestamp of the reference message
            ref_message = self.db.query(Message).filter(
                Message.id == up_to_message_id
            ).first()
            if ref_message:
                query = query.filter(Message.created_at <= ref_message.created_at)
        
        messages = query.all()
        count = 0
        current_time = datetime.utcnow()
        
        for message in messages:
            message.status = MessageStatus.READ
            message.read_at = current_time
            if message.delivered_at is None:
                message.delivered_at = current_time
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count
    
    def get_unread_message_count(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """
        Get count of unread messages in a chat for a user.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            int: Number of unread messages
        """
        return self.db.query(Message).filter(
            and_(
                Message.chat_id == chat_id,
                Message.sender_id != user_id,  # Don't count own messages
                Message.is_deleted == False,
                or_(
                    Message.status == MessageStatus.SENT,
                    Message.status == MessageStatus.DELIVERED
                )
            )
        ).count()
    
    def search_messages(self, chat_id: uuid.UUID, query: str, limit: int = 20) -> List[Message]:
        """
        Search messages in a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            List[Message]: List of matching messages
        """
        return self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            and_(
                Message.chat_id == chat_id,
                Message.message_type == MessageType.TEXT,
                Message.content.ilike(f"%{query}%"),
                Message.is_deleted == False
            )
        ).order_by(desc(Message.created_at)).limit(limit).all()
    
    def get_chat_media_messages(self, chat_id: uuid.UUID, message_types: List[MessageType],
                               limit: int = 50) -> List[Message]:
        """
        Get media messages from a chat.
        
        Args:
            chat_id (uuid.UUID): Chat's unique identifier
            message_types (List[MessageType]): List of message types to filter
            limit (int): Maximum number of messages
            
        Returns:
            List[Message]: List of media messages
        """
        return self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            and_(
                Message.chat_id == chat_id,
                Message.message_type.in_(message_types),
                Message.is_deleted == False
            )
        ).order_by(desc(Message.created_at)).limit(limit).all()
    
    def update_message_file_info(self, message_id: uuid.UUID, file_url: str,
                                file_name: str, file_size: int, 
                                thumbnail_url: Optional[str] = None) -> bool:
        """
        Update message with file information after upload.
        
        Args:
            message_id (uuid.UUID): Message's unique identifier
            file_url (str): URL to uploaded file
            file_name (str): Original file name
            file_size (int): File size in bytes
            thumbnail_url (Optional[str]): URL to thumbnail
            
        Returns:
            bool: True if updated successfully
        """
        db_message = self.get_message_by_id(message_id)
        if not db_message:
            return False
        
        db_message.file_url = file_url
        db_message.file_name = file_name
        db_message.file_size = file_size
        if thumbnail_url:
            db_message.thumbnail_url = thumbnail_url
        
        self.db.commit()
        return True
