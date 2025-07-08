"""
Location tracking repository for database operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from app.models.location import (
    UserLocation, LocationShare, LocationHistory, GeofenceArea, GeofenceEvent
)
from app.schemas.location import (
    UserLocationCreate, UserLocationUpdate, LocationShareCreate, LocationShareUpdate,
    GeofenceAreaCreate, GeofenceAreaUpdate
)
import math


class LocationRepository:
    """Repository for location operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_location(self, user_id: int, location_data: UserLocationCreate) -> UserLocation:
        """Create a new user location."""
        # If this is set as current, update previous current locations
        if location_data.is_current:
            self.db.query(UserLocation).filter(
                and_(
                    UserLocation.user_id == user_id,
                    UserLocation.is_current == True
                )
            ).update({"is_current": False})
        
        db_location = UserLocation(
            user_id=user_id,
            **location_data.dict()
        )
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location

    def get_location_by_id(self, location_id: int) -> Optional[UserLocation]:
        """Get a location by ID."""
        return self.db.query(UserLocation).filter(UserLocation.id == location_id).first()

    def get_user_current_location(self, user_id: int) -> Optional[UserLocation]:
        """Get user's current location."""
        return (
            self.db.query(UserLocation)
            .filter(
                and_(
                    UserLocation.user_id == user_id,
                    UserLocation.is_current == True
                )
            )
            .order_by(desc(UserLocation.location_timestamp))
            .first()
        )

    def get_user_locations(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0,
        location_type: Optional[str] = None
    ) -> List[UserLocation]:
        """Get user's location history."""
        query = self.db.query(UserLocation).filter(UserLocation.user_id == user_id)
        
        if location_type:
            query = query.filter(UserLocation.location_type == location_type)
        
        return (
            query
            .order_by(desc(UserLocation.location_timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_location(
        self, 
        location_id: int, 
        user_id: int, 
        location_data: UserLocationUpdate
    ) -> Optional[UserLocation]:
        """Update a user location."""
        db_location = (
            self.db.query(UserLocation)
            .filter(
                and_(
                    UserLocation.id == location_id,
                    UserLocation.user_id == user_id
                )
            )
            .first()
        )
        
        if not db_location:
            return None

        update_data = location_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_location, field, value)

        self.db.commit()
        self.db.refresh(db_location)
        return db_location

    def delete_location(self, location_id: int, user_id: int) -> bool:
        """Delete a user location."""
        db_location = (
            self.db.query(UserLocation)
            .filter(
                and_(
                    UserLocation.id == location_id,
                    UserLocation.user_id == user_id
                )
            )
            .first()
        )
        
        if not db_location:
            return False

        self.db.delete(db_location)
        self.db.commit()
        return True

    def find_nearby_users(
        self, 
        latitude: float, 
        longitude: float, 
        radius: float,
        user_id: int,
        limit: int = 10
    ) -> List[Tuple[UserLocation, float]]:
        """Find users with shared locations within radius."""
        # Using Haversine formula for distance calculation
        # This is a simplified version - in production, consider using PostGIS
        
        # Convert radius from meters to degrees (rough approximation)
        radius_deg = radius / 111000  # 111km per degree
        
        nearby_locations = (
            self.db.query(UserLocation)
            .filter(
                and_(
                    UserLocation.user_id != user_id,
                    UserLocation.is_current == True,
                    UserLocation.is_shared == True,
                    UserLocation.latitude.between(latitude - radius_deg, latitude + radius_deg),
                    UserLocation.longitude.between(longitude - radius_deg, longitude + radius_deg)
                )
            )
            .limit(limit * 2)  # Get more results to filter by exact distance
            .all()
        )
        
        # Calculate exact distances and filter
        results = []
        for location in nearby_locations:
            distance = self._calculate_distance(
                latitude, longitude, 
                location.latitude, location.longitude
            )
            if distance <= radius:
                results.append((location, distance))
        
        # Sort by distance and limit results
        results.sort(key=lambda x: x[1])
        return results[:limit]

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def cleanup_old_locations(self, days: int = 30) -> int:
        """Clean up old location data."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = (
            self.db.query(UserLocation)
            .filter(
                and_(
                    UserLocation.is_current == False,
                    UserLocation.created_at < cutoff_date
                )
            )
            .delete()
        )
        
        self.db.commit()
        return deleted_count


class LocationShareRepository:
    """Repository for location sharing operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_location_share(
        self, 
        user_id: int, 
        share_data: LocationShareCreate
    ) -> LocationShare:
        """Create a new location share."""
        # Calculate expiration time if duration is specified
        expires_at = None
        if share_data.duration_minutes:
            expires_at = datetime.utcnow() + timedelta(minutes=share_data.duration_minutes)
        
        db_share = LocationShare(
            user_id=user_id,
            expires_at=expires_at,
            **share_data.dict()
        )
        self.db.add(db_share)
        self.db.commit()
        self.db.refresh(db_share)
        return db_share

    def get_location_share_by_id(self, share_id: int) -> Optional[LocationShare]:
        """Get a location share by ID."""
        return self.db.query(LocationShare).filter(LocationShare.id == share_id).first()

    def get_user_location_shares(
        self, 
        user_id: int, 
        active_only: bool = True
    ) -> List[LocationShare]:
        """Get user's location shares."""
        query = self.db.query(LocationShare).filter(LocationShare.user_id == user_id)
        
        if active_only:
            current_time = datetime.utcnow()
            query = query.filter(
                and_(
                    LocationShare.is_active == True,
                    or_(
                        LocationShare.expires_at.is_(None),
                        LocationShare.expires_at > current_time
                    )
                )
            )
        
        return query.order_by(desc(LocationShare.started_at)).all()

    def get_shared_locations_for_user(self, user_id: int) -> List[LocationShare]:
        """Get locations shared with a specific user."""
        current_time = datetime.utcnow()
        
        return (
            self.db.query(LocationShare)
            .filter(
                and_(
                    LocationShare.shared_with_user_id == user_id,
                    LocationShare.is_active == True,
                    or_(
                        LocationShare.expires_at.is_(None),
                        LocationShare.expires_at > current_time
                    )
                )
            )
            .order_by(desc(LocationShare.started_at))
            .all()
        )

    def get_shared_locations_for_chat(self, chat_id: int) -> List[LocationShare]:
        """Get locations shared with a specific chat."""
        current_time = datetime.utcnow()
        
        return (
            self.db.query(LocationShare)
            .filter(
                and_(
                    LocationShare.shared_with_chat_id == chat_id,
                    LocationShare.is_active == True,
                    or_(
                        LocationShare.expires_at.is_(None),
                        LocationShare.expires_at > current_time
                    )
                )
            )
            .order_by(desc(LocationShare.started_at))
            .all()
        )

    def update_location_share(
        self, 
        share_id: int, 
        user_id: int, 
        share_data: LocationShareUpdate
    ) -> Optional[LocationShare]:
        """Update a location share."""
        db_share = (
            self.db.query(LocationShare)
            .filter(
                and_(
                    LocationShare.id == share_id,
                    LocationShare.user_id == user_id
                )
            )
            .first()
        )
        
        if not db_share:
            return None

        update_data = share_data.dict(exclude_unset=True)
        
        # Update expiration if duration changed
        if "duration_minutes" in update_data and update_data["duration_minutes"]:
            update_data["expires_at"] = datetime.utcnow() + timedelta(
                minutes=update_data["duration_minutes"]
            )
            del update_data["duration_minutes"]
        
        for field, value in update_data.items():
            setattr(db_share, field, value)

        self.db.commit()
        self.db.refresh(db_share)
        return db_share

    def stop_location_share(self, share_id: int, user_id: int) -> bool:
        """Stop a location share."""
        db_share = (
            self.db.query(LocationShare)
            .filter(
                and_(
                    LocationShare.id == share_id,
                    LocationShare.user_id == user_id
                )
            )
            .first()
        )
        
        if not db_share:
            return False
        
        db_share.is_active = False
        db_share.stopped_at = datetime.utcnow()
        self.db.commit()
        return True

    def cleanup_expired_shares(self) -> int:
        """Clean up expired location shares."""
        current_time = datetime.utcnow()
        
        updated_count = (
            self.db.query(LocationShare)
            .filter(
                and_(
                    LocationShare.is_active == True,
                    LocationShare.expires_at.isnot(None),
                    LocationShare.expires_at <= current_time
                )
            )
            .update({
                "is_active": False,
                "stopped_at": current_time
            })
        )
        
        self.db.commit()
        return updated_count


class GeofenceRepository:
    """Repository for geofence operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_geofence(self, user_id: int, geofence_data: GeofenceAreaCreate) -> GeofenceArea:
        """Create a new geofence area."""
        db_geofence = GeofenceArea(
            user_id=user_id,
            **geofence_data.dict()
        )
        self.db.add(db_geofence)
        self.db.commit()
        self.db.refresh(db_geofence)
        return db_geofence

    def get_geofence_by_id(self, geofence_id: int) -> Optional[GeofenceArea]:
        """Get a geofence by ID."""
        return self.db.query(GeofenceArea).filter(GeofenceArea.id == geofence_id).first()

    def get_user_geofences(self, user_id: int, active_only: bool = True) -> List[GeofenceArea]:
        """Get user's geofences."""
        query = self.db.query(GeofenceArea).filter(GeofenceArea.user_id == user_id)
        
        if active_only:
            query = query.filter(GeofenceArea.is_active == True)
        
        return query.order_by(GeofenceArea.name).all()

    def update_geofence(
        self, 
        geofence_id: int, 
        user_id: int, 
        geofence_data: GeofenceAreaUpdate
    ) -> Optional[GeofenceArea]:
        """Update a geofence area."""
        db_geofence = (
            self.db.query(GeofenceArea)
            .filter(
                and_(
                    GeofenceArea.id == geofence_id,
                    GeofenceArea.user_id == user_id
                )
            )
            .first()
        )
        
        if not db_geofence:
            return None

        update_data = geofence_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_geofence, field, value)

        self.db.commit()
        self.db.refresh(db_geofence)
        return db_geofence

    def delete_geofence(self, geofence_id: int, user_id: int) -> bool:
        """Delete a geofence area."""
        db_geofence = (
            self.db.query(GeofenceArea)
            .filter(
                and_(
                    GeofenceArea.id == geofence_id,
                    GeofenceArea.user_id == user_id
                )
            )
            .first()
        )
        
        if not db_geofence:
            return False

        self.db.delete(db_geofence)
        self.db.commit()
        return True

    def check_geofence_triggers(
        self, 
        user_id: int, 
        latitude: float, 
        longitude: float
    ) -> List[Tuple[GeofenceArea, str]]:
        """Check if a location triggers any geofences."""
        geofences = self.get_user_geofences(user_id, active_only=True)
        triggered = []
        
        for geofence in geofences:
            distance = self._calculate_distance(
                latitude, longitude,
                geofence.center_latitude, geofence.center_longitude
            )
            
            if distance <= geofence.radius:
                # Inside geofence
                if geofence.trigger_on_enter:
                    triggered.append((geofence, "enter"))
            else:
                # Outside geofence - would need to track previous state for exit events
                # This is simplified - in production, you'd track the previous location state
                pass
        
        return triggered

    def create_geofence_event(
        self,
        user_id: int,
        geofence_id: int,
        event_type: str,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None
    ) -> GeofenceEvent:
        """Create a geofence event."""
        db_event = GeofenceEvent(
            user_id=user_id,
            geofence_id=geofence_id,
            event_type=event_type,
            location_latitude=latitude,
            location_longitude=longitude,
            accuracy=accuracy,
            event_timestamp=datetime.utcnow()
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def get_geofence_events(
        self, 
        user_id: int, 
        geofence_id: Optional[int] = None,
        limit: int = 50
    ) -> List[GeofenceEvent]:
        """Get geofence events."""
        query = self.db.query(GeofenceEvent).filter(GeofenceEvent.user_id == user_id)
        
        if geofence_id:
            query = query.filter(GeofenceEvent.geofence_id == geofence_id)
        
        return (
            query
            .order_by(desc(GeofenceEvent.event_timestamp))
            .limit(limit)
            .all()
        )

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
