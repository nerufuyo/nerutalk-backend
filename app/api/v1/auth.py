from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserCreate, UserLogin, UserUpdate, UserResponse, 
    TokenResponse, TokenRefresh, ChangePassword
)
from app.models.user import User
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency to get authentication service instance.
    
    Args:
        db (Session): Database session
        
    Returns:
        AuthService: Authentication service instance
    """
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token
        auth_service (AuthService): Authentication service
        
    Returns:
        User: Current authenticated user
    """
    return auth_service.get_current_user(credentials.credentials)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    
    Args:
        user_data (UserCreate): User registration data
        auth_service (AuthService): Authentication service
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If email or username already exists
    """
    return auth_service.register_user(user_data)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return access tokens.
    
    Args:
        login_data (UserLogin): User login credentials
        auth_service (AuthService): Authentication service
        
    Returns:
        TokenResponse: Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    return auth_service.authenticate_user(login_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    
    Args:
        token_data (TokenRefresh): Refresh token data
        auth_service (AuthService): Authentication service
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    return auth_service.refresh_access_token(token_data.refresh_token)


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current user.
    
    Args:
        current_user (User): Current authenticated user
        auth_service (AuthService): Authentication service
        
    Returns:
        dict: Success message
    """
    auth_service.logout_user(current_user.id)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Args:
        current_user (User): Current authenticated user
        
    Returns:
        UserResponse: Current user's profile
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user's profile information.
    
    Args:
        user_data (UserUpdate): Updated user data
        current_user (User): Current authenticated user
        auth_service (AuthService): Authentication service
        
    Returns:
        UserResponse: Updated user profile
    """
    return auth_service.update_user_profile(current_user.id, user_data)


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change current user's password.
    
    Args:
        password_data (ChangePassword): Password change data
        current_user (User): Current authenticated user
        auth_service (AuthService): Authentication service
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    auth_service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user profile by ID.
    
    Args:
        user_id (uuid.UUID): User's unique identifier
        current_user (User): Current authenticated user
        auth_service (AuthService): Authentication service
        
    Returns:
        UserResponse: User profile data
        
    Raises:
        HTTPException: If user not found
    """
    return auth_service.get_user_profile(user_id)


@router.post("/verify-email")
async def verify_email(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify current user's email address.
    
    Args:
        current_user (User): Current authenticated user
        auth_service (AuthService): Authentication service
        
    Returns:
        dict: Success message
    """
    auth_service.verify_user_email(current_user.id)
    return {"message": "Email verified successfully"}
