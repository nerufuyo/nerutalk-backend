"""
Location tracking schemas for request/response data validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class UserLocationBase(BaseModel):
    """Base schema for user locations."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: Optional[float] = Field(None, ge=0)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    location_type: Optional[str] = None
    provider: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0)
    bearing: Optional[float] = Field(None, ge=0, lt=360)


class UserLocationCreate(UserLocationBase):
    """Schema for creating a user location."""
    location_timestamp: datetime
    is_current: bool = True
    is_shared: bool = False


class UserLocationUpdate(BaseModel):
    """Schema for updating a user location."""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    location_type: Optional[str] = None
    is_current: Optional[bool] = None
    is_shared: Optional[bool] = None


class UserLocationResponse(UserLocationBase):
    """Schema for user location response."""
    id: int
    user_id: int
    is_current: bool
    is_shared: bool
    location_timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationShareBase(BaseModel):
    """Base schema for location sharing."""
    shared_with_user_id: Optional[int] = None
    shared_with_chat_id: Optional[int] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_live: bool = True
    update_interval: int = Field(30, ge=10, le=300)  # 10 seconds to 5 minutes

    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duration must be positive')
        return v

    @validator('shared_with_user_id', 'shared_with_chat_id')
    def validate_share_target(cls, v, values):
        # Ensure at least one target is specified
        if 'shared_with_user_id' in values and 'shared_with_chat_id' in values:
            if not values.get('shared_with_user_id') and not values.get('shared_with_chat_id') and not v:
                raise ValueError('Must specify either shared_with_user_id or shared_with_chat_id')
        return v


class LocationShareCreate(LocationShareBase):
    """Schema for creating location share."""
    location_id: int


class LocationShareUpdate(BaseModel):
    """Schema for updating location share."""
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_live: Optional[bool] = None
    update_interval: Optional[int] = Field(None, ge=10, le=300)
    is_active: Optional[bool] = None


class LocationShareResponse(LocationShareBase):
    """Schema for location share response."""
    id: int
    user_id: int
    location_id: int
    is_active: bool
    started_at: datetime
    expires_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    location: Optional[UserLocationResponse] = None

    class Config:
        from_attributes = True


class GeofenceAreaBase(BaseModel):
    """Base schema for geofence areas."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    center_latitude: float = Field(..., ge=-90, le=90)
    center_longitude: float = Field(..., ge=-180, le=180)
    radius: float = Field(..., gt=0, le=10000)  # Max 10km radius
    fence_type: str = Field(default="circular")
    trigger_on_enter: bool = True
    trigger_on_exit: bool = True


class GeofenceAreaCreate(GeofenceAreaBase):
    """Schema for creating a geofence area."""
    pass


class GeofenceAreaUpdate(BaseModel):
    """Schema for updating a geofence area."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    center_latitude: Optional[float] = Field(None, ge=-90, le=90)
    center_longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius: Optional[float] = Field(None, gt=0, le=10000)
    trigger_on_enter: Optional[bool] = None
    trigger_on_exit: Optional[bool] = None
    is_active: Optional[bool] = None


class GeofenceAreaResponse(GeofenceAreaBase):
    """Schema for geofence area response."""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GeofenceEventResponse(BaseModel):
    """Schema for geofence event response."""
    id: int
    user_id: int
    geofence_id: int
    event_type: str
    location_latitude: float
    location_longitude: float
    accuracy: Optional[float] = None
    confidence: Optional[float] = None
    is_processed: bool
    notification_sent: bool
    event_timestamp: datetime
    created_at: datetime
    geofence: Optional[GeofenceAreaResponse] = None

    class Config:
        from_attributes = True


class LocationHistoryResponse(BaseModel):
    """Schema for location history response."""
    id: int
    user_id: int
    start_latitude: float
    start_longitude: float
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    activity_type: Optional[str] = None
    confidence: Optional[float] = None
    distance: Optional[float] = None
    duration: Optional[int] = None
    average_speed: Optional[float] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LocationUpdateRequest(BaseModel):
    """Schema for live location updates."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: Optional[float] = Field(None, ge=0)
    speed: Optional[float] = Field(None, ge=0)
    bearing: Optional[float] = Field(None, ge=0, lt=360)
    provider: Optional[str] = None
    timestamp: datetime


class NearbyUsersRequest(BaseModel):
    """Schema for finding nearby users."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius: float = Field(..., gt=0, le=10000)  # Max 10km radius
    limit: int = Field(10, ge=1, le=50)


class NearbyUserResponse(BaseModel):
    """Schema for nearby user response."""
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    distance: float  # Distance in meters
    last_seen: datetime
    is_sharing_location: bool


class LocationStatsResponse(BaseModel):
    """Schema for location statistics."""
    total_locations: int
    active_shares: int
    geofences_count: int
    recent_events: int
    most_visited_places: List[dict]
    activity_summary: dict


class BatchLocationUpdate(BaseModel):
    """Schema for batch location updates."""
    locations: List[LocationUpdateRequest] = Field(..., min_items=1, max_items=100)


class LocationPrivacySettings(BaseModel):
    """Schema for location privacy settings."""
    share_location_default: bool = False
    allow_nearby_discovery: bool = True
    location_history_enabled: bool = True
    geofence_notifications: bool = True
    data_retention_days: int = Field(30, ge=1, le=365)
