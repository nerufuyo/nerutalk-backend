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
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # Security settings
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Legacy aliases for compatibility
    @property
    def algorithm(self) -> str:
        return self.jwt_algorithm
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.jwt_access_token_expire_minutes
    
    @property
    def refresh_token_expire_days(self) -> int:
        return self.jwt_refresh_token_expire_days
    
    # AWS S3 settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_bucket_name: Optional[str] = None  # Legacy alias
    aws_region: str = "us-west-2"
    
    # File upload settings
    max_file_size: int = 10485760  # 10MB
    allowed_file_extensions: str = "jpg,jpeg,png,gif,webp,mp4,mov,avi,mkv,pdf,doc,docx,txt"
    allowed_image_extensions: str = "jpg,jpeg,png,gif,webp"
    allowed_video_extensions: str = "mp4,mov,avi,mkv"
    thumbnail_size: int = 300
    thumbnail_quality: int = 85
    
    # Firebase settings
    firebase_server_key: Optional[str] = None
    fcm_server_key: Optional[str] = None  # Alias
    firebase_project_id: Optional[str] = None
    fcm_project_id: Optional[str] = None  # Alias
    fcm_credentials_file: Optional[str] = None
    
    # Video call service settings (Agora.io)
    agora_app_id: Optional[str] = None
    agora_app_certificate: Optional[str] = None
    agora_token_expiry_hours: int = 24
    
    # External APIs
    giphy_api_key: Optional[str] = None
    tenor_api_key: Optional[str] = None
    
    # Email settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # Security & CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"
    trusted_hosts: str = "localhost,127.0.0.1"
    bcrypt_rounds: int = 12
    
    # Language & Internationalization
    default_language: str = "en"
    supported_languages: str = "en,id,jp,ko,cn"
    auto_detect_language: bool = True
    
    # Background Tasks (Celery)
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Rate limiting settings
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # Location tracking
    location_accuracy_threshold: int = 100  # meters
    location_history_retention_days: int = 90
    geofence_max_radius: int = 10000  # meters
    
    # Notification settings
    notification_batch_size: int = 1000
    notification_retry_attempts: int = 3
    notification_cleanup_days: int = 30
    
    # WebSocket configuration
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    websocket_max_connections: int = 10000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/nerutalk.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Cache configuration
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000
    
    # Production settings
    use_https: bool = False
    secure_cookies: bool = False
    secure_headers: bool = False
    
    # Expose uppercase properties for service usage
    @property
    def AGORA_APP_ID(self) -> Optional[str]:
        return self.agora_app_id
    
    @property
    def AGORA_APP_CERTIFICATE(self) -> Optional[str]:
        return self.agora_app_certificate
    
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
