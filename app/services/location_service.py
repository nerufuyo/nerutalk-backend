"""
Location service for handling GPS, location sharing, and geofencing operations.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.location import LocationShare, GeofenceArea, GeofenceEvent
from app.repositories.location_repository import LocationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.location import (
    UserLocationCreate, UserLocationUpdate, UserLocationResponse,
    LocationShareCreate, LocationShareUpdate, LocationShareResponse,
    LocationHistoryResponse, GeofenceAreaCreate, GeofenceAreaUpdate, GeofenceAreaResponse,
    GeofenceEventResponse, NearbyUsersResponse, LocationStatsResponse
)
from app.services.push_notification_service import PushNotificationService
from app.schemas.push_notification import SystemNotificationData
import math

logger = logging.getLogger(__name__)


class LocationService:
    """Service for location tracking and geofencing operations."""

    def __init__(self, db: Session):
        self.db = db
        self.location_repo = LocationRepository(db)
        self.user_repo = UserRepository(db)
        self.notification_service = PushNotificationService(db)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r * 1000  # Return distance in meters

    async def update_user_location(
        self,
        user_id: int,
        location_data: UserLocationCreate
    ) -> UserLocationResponse:
        """Update user's current location."""
        try:
            # Verify user exists
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Check location accuracy and validity
            if location_data.accuracy and location_data.accuracy > 100:  # 100 meters
                logger.warning(f"Low accuracy location update for user {user_id}: {location_data.accuracy}m")
            
            # Create or update location
            location = self.location_repo.create_location(user_id, location_data)
            
            # Check geofence triggers
            await self._check_geofence_triggers(user_id, location_data.latitude, location_data.longitude)
            
            # Notify location shares if user has active shares
            await self._notify_location_shares(user_id, location)
            
            logger.info(f"Location updated for user {user_id}: {location.latitude}, {location.longitude}")
            return UserLocationResponse.from_orm(location)
            
        except Exception as e:
            logger.error(f"Error updating user location: {str(e)}")
            raise

    async def get_user_location(self, user_id: int, requester_id: int) -> Optional[UserLocationResponse]:
        """Get user's current location if sharing is enabled."""
        try:
            # Check if user is sharing location with requester
            if not await self._can_access_location(user_id, requester_id):
                return None
            
            location = self.location_repo.get_current_location(user_id)
            if location:
                return UserLocationResponse.from_orm(location)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user location: {str(e)}")
            raise

    async def get_location_history(
        self,
        user_id: int,
        requester_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LocationHistoryResponse]:
        """Get user's location history if sharing is enabled."""
        try:
            # Check if user is sharing location with requester
            if not await self._can_access_location(user_id, requester_id):
                return []
            
            locations = self.location_repo.get_location_history(
                user_id, start_time, end_time, limit
            )
            
            return [LocationHistoryResponse.from_orm(loc) for loc in locations]
            
        except Exception as e:
            logger.error(f"Error getting location history: {str(e)}")
            raise

    async def create_location_share(
        self,
        user_id: int,
        share_data: LocationShareCreate
    ) -> LocationShareResponse:
        """Create a new location share."""
        try:
            # Verify target user exists if specified
            if share_data.target_user_id:
                target_user = self.user_repo.get_user_by_id(share_data.target_user_id)
                if not target_user:
                    raise ValueError("Target user not found")
            
            # Create location share
            location_share = self.location_repo.create_location_share(user_id, share_data)
            
            # Send notification to target user
            if share_data.target_user_id:
                await self._notify_location_share_created(user_id, share_data.target_user_id)
            
            logger.info(f"Location share created: {location_share.id}")
            return LocationShareResponse.from_orm(location_share)
            
        except Exception as e:
            logger.error(f"Error creating location share: {str(e)}")
            raise

    async def update_location_share(
        self,
        share_id: int,
        user_id: int,
        share_data: LocationShareUpdate
    ) -> Optional[LocationShareResponse]:
        """Update a location share."""
        try:
            # Verify share belongs to user
            location_share = self.location_repo.get_location_share_by_id(share_id)
            if not location_share or location_share.user_id != user_id:
                return None
            
            updated_share = self.location_repo.update_location_share(share_id, share_data)
            if updated_share:
                return LocationShareResponse.from_orm(updated_share)
            return None
            
        except Exception as e:
            logger.error(f"Error updating location share: {str(e)}")
            raise

    async def delete_location_share(self, share_id: int, user_id: int) -> bool:
        """Delete a location share."""
        try:
            location_share = self.location_repo.get_location_share_by_id(share_id)
            if not location_share or location_share.user_id != user_id:
                return False
            
            # Notify target user if applicable
            if location_share.target_user_id:
                await self._notify_location_share_ended(user_id, location_share.target_user_id)
            
            return self.location_repo.delete_location_share(share_id)
            
        except Exception as e:
            logger.error(f"Error deleting location share: {str(e)}")
            raise

    async def get_user_location_shares(self, user_id: int) -> List[LocationShareResponse]:
        """Get all location shares for a user."""
        shares = self.location_repo.get_location_shares_by_user(user_id)
        return [LocationShareResponse.from_orm(share) for share in shares]

    async def find_nearby_users(
        self,
        user_id: int,
        radius_meters: int = 1000,
        limit: int = 50
    ) -> List[NearbyUsersResponse]:
        """Find nearby users within specified radius."""
        try:
            # Get user's current location
            current_location = self.location_repo.get_current_location(user_id)
            if not current_location:
                return []
            
            # Find nearby users
            nearby_users = self.location_repo.find_nearby_users(
                current_location.latitude,
                current_location.longitude,
                radius_meters,
                exclude_user_id=user_id,
                limit=limit
            )
            
            result = []
            for user_location in nearby_users:
                # Check if we can access this user's location
                if await self._can_access_location(user_location.user_id, user_id):
                    distance = self.calculate_distance(
                        current_location.latitude,
                        current_location.longitude,
                        user_location.latitude,
                        user_location.longitude
                    )
                    
                    user = self.user_repo.get_user_by_id(user_location.user_id)
                    result.append(NearbyUsersResponse(
                        user_id=user_location.user_id,
                        username=user.username if user else "Unknown",
                        display_name=user.display_name if user else None,
                        distance_meters=round(distance),
                        last_seen=user_location.created_at
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding nearby users: {str(e)}")
            raise

    async def create_geofence_area(
        self,
        user_id: int,
        geofence_data: GeofenceAreaCreate
    ) -> GeofenceAreaResponse:
        """Create a new geofence area."""
        try:
            geofence = self.location_repo.create_geofence_area(user_id, geofence_data)
            
            logger.info(f"Geofence area created: {geofence.id}")
            return GeofenceAreaResponse.from_orm(geofence)
            
        except Exception as e:
            logger.error(f"Error creating geofence area: {str(e)}")
            raise

    async def update_geofence_area(
        self,
        geofence_id: int,
        user_id: int,
        geofence_data: GeofenceAreaUpdate
    ) -> Optional[GeofenceAreaResponse]:
        """Update a geofence area."""
        try:
            # Verify geofence belongs to user
            geofence = self.location_repo.get_geofence_area_by_id(geofence_id)
            if not geofence or geofence.user_id != user_id:
                return None
            
            updated_geofence = self.location_repo.update_geofence_area(geofence_id, geofence_data)
            if updated_geofence:
                return GeofenceAreaResponse.from_orm(updated_geofence)
            return None
            
        except Exception as e:
            logger.error(f"Error updating geofence area: {str(e)}")
            raise

    async def delete_geofence_area(self, geofence_id: int, user_id: int) -> bool:
        """Delete a geofence area."""
        try:
            geofence = self.location_repo.get_geofence_area_by_id(geofence_id)
            if not geofence or geofence.user_id != user_id:
                return False
            
            return self.location_repo.delete_geofence_area(geofence_id)
            
        except Exception as e:
            logger.error(f"Error deleting geofence area: {str(e)}")
            raise

    async def get_user_geofence_areas(self, user_id: int) -> List[GeofenceAreaResponse]:
        """Get all geofence areas for a user."""
        geofences = self.location_repo.get_geofence_areas_by_user(user_id)
        return [GeofenceAreaResponse.from_orm(geofence) for geofence in geofences]

    async def get_geofence_events(
        self,
        user_id: int,
        geofence_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[GeofenceEventResponse]:
        """Get geofence events for a user."""
        events = self.location_repo.get_geofence_events(
            user_id, geofence_id, start_time, end_time, limit
        )
        return [GeofenceEventResponse.from_orm(event) for event in events]

    async def get_location_stats(self, user_id: int, days: int = 30) -> LocationStatsResponse:
        """Get location statistics for a user."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Get location history count
            locations = self.location_repo.get_location_history(
                user_id, start_time, end_time, limit=10000
            )
            
            # Calculate basic stats
            total_locations = len(locations)
            active_shares = len(self.location_repo.get_active_location_shares(user_id))
            geofence_areas = len(self.location_repo.get_geofence_areas_by_user(user_id))
            
            # Get geofence events
            geofence_events = self.location_repo.get_geofence_events(
                user_id, start_time=start_time, end_time=end_time, limit=1000
            )
            
            return LocationStatsResponse(
                total_locations=total_locations,
                active_shares=active_shares,
                geofence_areas=geofence_areas,
                geofence_events=len(geofence_events),
                days_tracked=days
            )
            
        except Exception as e:
            logger.error(f"Error getting location stats: {str(e)}")
            raise

    async def cleanup_old_location_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old location data."""
        try:
            return self.location_repo.cleanup_old_data(days)
            
        except Exception as e:
            logger.error(f"Error cleaning up old location data: {str(e)}")
            raise

    # Private helper methods

    async def _can_access_location(self, user_id: int, requester_id: int) -> bool:
        """Check if requester can access user's location."""
        if user_id == requester_id:
            return True
        
        # Check active location shares
        active_shares = self.location_repo.get_active_location_shares(user_id)
        
        for share in active_shares:
            # Public share or specific user share
            if share.target_user_id is None or share.target_user_id == requester_id:
                return True
        
        return False

    async def _check_geofence_triggers(self, user_id: int, latitude: float, longitude: float):
        """Check for geofence triggers and create events."""
        try:
            geofence_areas = self.location_repo.get_geofence_areas_by_user(user_id, active_only=True)
            
            for geofence in geofence_areas:
                distance = self.calculate_distance(
                    latitude, longitude,
                    geofence.center_latitude, geofence.center_longitude
                )
                
                is_inside = distance <= geofence.radius_meters
                
                # Check for entry/exit events
                last_event = self.location_repo.get_last_geofence_event(user_id, geofence.id)
                
                if is_inside and (not last_event or last_event.event_type == "exit"):
                    # Entry event
                    self.location_repo.create_geofence_event(
                        user_id, geofence.id, "entry", latitude, longitude
                    )
                    
                    # Send notification if enabled
                    if geofence.notify_on_entry:
                        await self._send_geofence_notification(
                            user_id, geofence, "entry"
                        )
                
                elif not is_inside and last_event and last_event.event_type == "entry":
                    # Exit event
                    self.location_repo.create_geofence_event(
                        user_id, geofence.id, "exit", latitude, longitude
                    )
                    
                    # Send notification if enabled
                    if geofence.notify_on_exit:
                        await self._send_geofence_notification(
                            user_id, geofence, "exit"
                        )
                        
        except Exception as e:
            logger.error(f"Error checking geofence triggers: {str(e)}")

    async def _notify_location_shares(self, user_id: int, location):
        """Notify users who have access to this user's location."""
        try:
            # This could be implemented to send real-time location updates
            # to users who are sharing location with this user
            pass
        except Exception as e:
            logger.error(f"Error notifying location shares: {str(e)}")

    async def _notify_location_share_created(self, sharer_id: int, target_user_id: int):
        """Notify user that someone is sharing location with them."""
        try:
            sharer = self.user_repo.get_user_by_id(sharer_id)
            if sharer:
                system_data = SystemNotificationData(
                    action="location_share_created",
                    details={"sharer_name": sharer.display_name or sharer.username}
                )
                
                await self.notification_service.send_system_notification(
                    user_id=target_user_id,
                    system_data=system_data,
                    title="Location Share",
                    body=f"{sharer.display_name or sharer.username} is sharing their location with you"
                )
        except Exception as e:
            logger.error(f"Error notifying location share created: {str(e)}")

    async def _notify_location_share_ended(self, sharer_id: int, target_user_id: int):
        """Notify user that location sharing has ended."""
        try:
            sharer = self.user_repo.get_user_by_id(sharer_id)
            if sharer:
                system_data = SystemNotificationData(
                    action="location_share_ended",
                    details={"sharer_name": sharer.display_name or sharer.username}
                )
                
                await self.notification_service.send_system_notification(
                    user_id=target_user_id,
                    system_data=system_data,
                    title="Location Share Ended",
                    body=f"{sharer.display_name or sharer.username} stopped sharing their location"
                )
        except Exception as e:
            logger.error(f"Error notifying location share ended: {str(e)}")

    async def _send_geofence_notification(self, user_id: int, geofence: GeofenceArea, event_type: str):
        """Send geofence trigger notification."""
        try:
            system_data = SystemNotificationData(
                action=f"geofence_{event_type}",
                details={
                    "geofence_name": geofence.name,
                    "event_type": event_type
                }
            )
            
            title = f"Geofence {event_type.title()}"
            body = f"You have {event_type}ed {geofence.name}"
            
            await self.notification_service.send_system_notification(
                user_id=user_id,
                system_data=system_data,
                title=title,
                body=body
            )
        except Exception as e:
            logger.error(f"Error sending geofence notification: {str(e)}")
