from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.core.security import get_password_hash
import uuid


class UserRepository:
    """
    Repository class for User database operations.
    
    This class encapsulates all database operations related to users,
    providing a clean interface for the service layer.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_data (UserCreate): User creation data
            
        Returns:
            User: Created user instance
        """
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            bio=user_data.bio,
            phone_number=user_data.phone_number
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Get a user by their ID.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address.
        
        Args:
            email (str): User's email address
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by their username.
        
        Args:
            username (str): User's username
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email_or_username(self, identifier: str) -> Optional[User]:
        """
        Get a user by their email or username.
        
        Args:
            identifier (str): Email or username
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        return self.db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()
    
    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Update user profile information.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            user_data (UserUpdate): Updated user data
            
        Returns:
            Optional[User]: Updated user instance or None if not found
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user_password(self, user_id: uuid.UUID, new_password: str) -> Optional[User]:
        """
        Update user's password.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            new_password (str): New password (will be hashed)
            
        Returns:
            Optional[User]: Updated user instance or None if not found
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        db_user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def verify_user_email(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Mark user's email as verified.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            Optional[User]: Updated user instance or None if not found
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        db_user.is_verified = True
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def deactivate_user(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            Optional[User]: Updated user instance or None if not found
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        db_user.is_active = False
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_online_status(self, user_id: uuid.UUID, is_online: bool) -> Optional[User]:
        """
        Update user's online status.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            is_online (bool): Online status
            
        Returns:
            Optional[User]: Updated user instance or None if not found
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        db_user.is_online = is_online
        if not is_online:
            # Update last_seen when going offline
            from datetime import datetime
            db_user.last_seen = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def search_users(self, query: str, limit: int = 10) -> List[User]:
        """
        Search users by username or full name.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            List[User]: List of matching users
        """
        return self.db.query(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%")
            )
        ).filter(User.is_active == True).limit(limit).all()
    
    def check_username_exists(self, username: str) -> bool:
        """
        Check if username already exists.
        
        Args:
            username (str): Username to check
            
        Returns:
            bool: True if username exists, False otherwise
        """
        return self.db.query(User).filter(User.username == username).first() is not None
    
    def check_email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email (str): Email to check
            
        Returns:
            bool: True if email exists, False otherwise
        """
        return self.db.query(User).filter(User.email == email).first() is not None
