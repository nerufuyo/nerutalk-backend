"""
Location tracking models for the NeruTalk application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class UserLocation(Base):
    """User location model for GPS tracking."""
    __tablename__ = "user_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Location coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)  # Elevation in meters
    accuracy = Column(Float, nullable=True)  # Accuracy in meters
    
    # Address information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Location context
    location_type = Column(String(50), nullable=True)  # home, work, current, etc.
    is_current = Column(Boolean, default=True)  # Is this the current location
    is_shared = Column(Boolean, default=False)  # Is location shared with others
    
    # Metadata
    provider = Column(String(20), nullable=True)  # GPS, network, passive
    speed = Column(Float, nullable=True)  # Speed in m/s
    bearing = Column(Float, nullable=True)  # Direction in degrees
    
    # Timestamps
    location_timestamp = Column(DateTime, nullable=False)  # When location was recorded
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="locations")


class LocationShare(Base):
    """Location sharing model for sharing location with specific users/chats."""
    __tablename__ = "location_shares"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Who is sharing
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Individual user
    shared_with_chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=True)  # Chat group
    
    # Location reference
    location_id = Column(Integer, ForeignKey("user_locations.id"), nullable=False)
    
    # Sharing settings
    duration_minutes = Column(Integer, nullable=True)  # How long to share (null = indefinite)
    is_live = Column(Boolean, default=True)  # Live location vs static location
    update_interval = Column(Integer, default=30)  # Update interval in seconds
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    shared_with_chat = relationship("Chat", foreign_keys=[shared_with_chat_id])
    location = relationship("UserLocation")


class LocationHistory(Base):
    """Location history model for tracking user movement patterns."""
    __tablename__ = "location_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Start and end locations
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    end_latitude = Column(Float, nullable=True)
    end_longitude = Column(Float, nullable=True)
    
    # Activity detection
    activity_type = Column(String(50), nullable=True)  # walking, driving, stationary, etc.
    confidence = Column(Float, nullable=True)  # Confidence level of activity detection
    
    # Movement metrics
    distance = Column(Float, nullable=True)  # Distance traveled in meters
    duration = Column(Integer, nullable=True)  # Duration in seconds
    average_speed = Column(Float, nullable=True)  # Average speed in m/s
    
    # Privacy and retention
    is_anonymized = Column(Boolean, default=False)
    retention_days = Column(Integer, default=30)  # How long to keep this data
    
    # Timestamps
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class GeofenceArea(Base):
    """Geofence area model for location-based triggers."""
    __tablename__ = "geofence_areas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Geofence definition
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Center point and radius (for circular geofences)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius = Column(Float, nullable=False)  # Radius in meters
    
    # Geofence type and settings
    fence_type = Column(String(20), default="circular")  # circular, polygon (future)
    trigger_on_enter = Column(Boolean, default=True)
    trigger_on_exit = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="geofences")
    events = relationship("GeofenceEvent", back_populates="geofence")


class GeofenceEvent(Base):
    """Geofence event model for tracking enter/exit events."""
    __tablename__ = "geofence_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    geofence_id = Column(Integer, ForeignKey("geofence_areas.id"), nullable=False)
    
    # Event details
    event_type = Column(String(10), nullable=False)  # enter, exit
    location_latitude = Column(Float, nullable=False)
    location_longitude = Column(Float, nullable=False)
    
    # Metadata
    accuracy = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    
    # Timestamps
    event_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    geofence = relationship("GeofenceArea", back_populates="events")
