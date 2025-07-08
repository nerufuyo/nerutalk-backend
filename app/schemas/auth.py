from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate that username contains only alphanumeric characters and underscores."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()


class UserCreate(UserBase):
    """Schema for user registration."""
    
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that password and confirm_password match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    phone_number: Optional[str]
    is_active: bool
    is_verified: bool
    is_online: bool
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Schema for detailed user profile."""
    
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    phone_number: Optional[str]
    is_online: bool
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that password and confirm_password match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePassword(BaseModel):
    """Schema for changing password."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that password and confirm_password match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
