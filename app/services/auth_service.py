from typing import Optional, Tuple
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    UserCreate, UserLogin, UserUpdate, TokenResponse, 
    ChangePassword, UserResponse
)
from app.models.user import User
from app.core.security import (
    verify_password, create_access_token, create_refresh_token, 
    verify_token
)
from app.core.config import settings
from app.utils.language import get_text, SupportedLanguage, DEFAULT_LANGUAGE
import uuid


class AuthService:
    """
    Service class for authentication and user management operations.
    
    This class contains the business logic for user registration, login,
    token management, and user profile operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the service with a database session.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user account.
        
        Args:
            user_data (UserCreate): User registration data
            
        Returns:
            UserResponse: Created user data
            
        Raises:
            HTTPException: If email or username already exists
        """
        # Check if email already exists
        if self.user_repo.check_email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if self.user_repo.check_username_exists(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        db_user = self.user_repo.create_user(user_data)
        return UserResponse.from_orm(db_user)
    
    def authenticate_user(self, login_data: UserLogin) -> TokenResponse:
        """
        Authenticate user and generate tokens.
        
        Args:
            login_data (UserLogin): User login credentials
            
        Returns:
            TokenResponse: Access and refresh tokens
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        user = self.user_repo.get_user_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Update user online status
        self.user_repo.update_online_status(user.id, True)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token (str): Valid refresh token
            
        Returns:
            TokenResponse: New access and refresh tokens
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if user exists and is active
        user = self.user_repo.get_user_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated"
            )
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.
        
        Args:
            token (str): JWT access token
            
        Returns:
            User: Current user instance
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = self.user_repo.get_user_by_id(uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        return user
    
    def update_user_profile(self, user_id: uuid.UUID, user_data: UserUpdate) -> UserResponse:
        """
        Update user profile information.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            user_data (UserUpdate): Updated user data
            
        Returns:
            UserResponse: Updated user data
            
        Raises:
            HTTPException: If user not found
        """
        updated_user = self.user_repo.update_user(user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(updated_user)
    
    def change_password(self, user_id: uuid.UUID, password_data: ChangePassword) -> bool:
        """
        Change user's password.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            password_data (ChangePassword): Password change data
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            HTTPException: If current password is incorrect or user not found
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        self.user_repo.update_user_password(user_id, password_data.new_password)
        return True
    
    def get_user_profile(self, user_id: uuid.UUID) -> UserResponse:
        """
        Get user profile by ID.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            UserResponse: User profile data
            
        Raises:
            HTTPException: If user not found
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
    
    def logout_user(self, user_id: uuid.UUID) -> bool:
        """
        Logout user by updating online status.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            bool: True if logout successful
        """
        self.user_repo.update_online_status(user_id, False)
        return True
    
    def verify_user_email(self, user_id: uuid.UUID) -> bool:
        """
        Mark user's email as verified.
        
        Args:
            user_id (uuid.UUID): User's unique identifier
            
        Returns:
            bool: True if verification successful
            
        Raises:
            HTTPException: If user not found
        """
        user = self.user_repo.verify_user_email(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return True
