"""
Agora video calling service integration.
"""
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional
from agora_token_builder import RtcTokenBuilder
from app.core.config import settings


class AgoraService:
    """Service for Agora.io video calling integration."""

    def __init__(self):
        self.app_id = settings.AGORA_APP_ID
        self.app_certificate = settings.AGORA_APP_CERTIFICATE
        self.token_expiration_seconds = 3600  # 1 hour

    def generate_channel_name(self, caller_id: int, callee_id: int) -> str:
        """Generate a unique channel name for the call."""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"call_{caller_id}_{callee_id}_{timestamp}_{unique_id}"

    def generate_uid(self, user_id: int) -> int:
        """Generate a unique UID for Agora based on user ID."""
        # Use user ID with timestamp to ensure uniqueness
        timestamp = int(time.time()) % 100000  # Last 5 digits of timestamp
        return int(f"{user_id}{timestamp}")

    def generate_rtc_token(
        self,
        channel_name: str,
        uid: int,
        role: int = 1,  # 1 for publisher, 2 for subscriber
        expiration_seconds: Optional[int] = None
    ) -> tuple[str, datetime]:
        """
        Generate RTC token for video/audio calling.
        
        Args:
            channel_name: The channel name for the call
            uid: The user's UID for Agora
            role: The user's role (1 for publisher, 2 for subscriber)
            expiration_seconds: Token expiration time in seconds
            
        Returns:
            Tuple of (token, expiration_datetime)
        """
        if not self.app_id or not self.app_certificate:
            raise ValueError("Agora App ID and App Certificate must be configured")

        expiration = expiration_seconds or self.token_expiration_seconds
        expiration_time_in_seconds = int(time.time()) + expiration
        
        token = RtcTokenBuilder.buildTokenWithUid(
            self.app_id,
            self.app_certificate,
            channel_name,
            uid,
            role,
            expiration_time_in_seconds
        )
        
        expiration_datetime = datetime.utcnow() + timedelta(seconds=expiration)
        
        return token, expiration_datetime

    def generate_rtm_token(
        self,
        user_id: str,
        expiration_seconds: Optional[int] = None
    ) -> tuple[str, datetime]:
        """
        Generate RTM token for real-time messaging.
        
        Args:
            user_id: The user ID for RTM
            expiration_seconds: Token expiration time in seconds
            
        Returns:
            Tuple of (token, expiration_datetime)
        """
        if not self.app_id or not self.app_certificate:
            raise ValueError("Agora App ID and App Certificate must be configured")

        expiration = expiration_seconds or self.token_expiration_seconds
        expiration_time_in_seconds = int(time.time()) + expiration
        
        # Note: RTM token generation would require the RTM token builder
        # For now, we'll use the RTC token builder as a placeholder
        # In production, you should use the proper RTM token builder
        token = RtcTokenBuilder.buildTokenWithAccount(
            self.app_id,
            self.app_certificate,
            user_id,
            expiration_time_in_seconds
        )
        
        expiration_datetime = datetime.utcnow() + timedelta(seconds=expiration)
        
        return token, expiration_datetime

    def validate_token_expiration(self, expires_at: datetime) -> bool:
        """Check if a token is still valid."""
        return datetime.utcnow() < expires_at

    def get_remaining_time(self, expires_at: datetime) -> int:
        """Get remaining time in seconds for a token."""
        remaining = expires_at - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))


# Global Agora service instance
agora_service = AgoraService()
