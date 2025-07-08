from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings configuration.
    Uses pydantic-settings to load configuration from environment variables.
    """
    
    # Application settings
    app_name: str = "NeruTalk Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # Security settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # AWS S3 settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_bucket_name: Optional[str] = None
    aws_region: str = "us-west-2"
    
    # Firebase settings
    firebase_server_key: Optional[str] = None
    firebase_project_id: Optional[str] = None
    
    # Video call service settings
    agora_app_id: Optional[str] = None
    agora_app_certificate: Optional[str] = None
    
    # Email settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # File upload settings
    max_file_size: int = 10485760  # 10MB
    allowed_image_extensions: str = "jpg,jpeg,png,gif,webp"
    allowed_video_extensions: str = "mp4,mov,avi,mkv"
    
    # Rate limiting settings
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
