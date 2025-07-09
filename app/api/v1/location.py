"""
Location tracking API endpoints for GPS, location sharing, and geofencing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.schemas.auth import UserResponse
from app.services.location_service import LocationService
from app.schemas.location import (
    UserLocationCreate, UserLocationUpdate, UserLocationResponse,
    LocationShareCreate, LocationShareUpdate, LocationShareResponse,
    LocationHistoryResponse, GeofenceAreaCreate, GeofenceAreaUpdate, GeofenceAreaResponse,
    GeofenceEventResponse, NearbyUsersResponse, LocationStatsResponse
)

router = APIRouter()


@router.post("/update", response_model=UserLocationResponse)
async def update_location(
    location_data: UserLocationCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's current location."""
    location_service = LocationService(db)
    return await location_service.update_user_location(current_user.id, location_data)


@router.get("/current/{user_id}", response_model=Optional[UserLocationResponse])
async def get_user_location(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current location if sharing is enabled."""
    location_service = LocationService(db)
    location = await location_service.get_user_location(user_id, current_user.id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not available or sharing not enabled"
        )
    return location


@router.get("/current", response_model=Optional[UserLocationResponse])
async def get_my_location(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's location."""
    location_service = LocationService(db)
    return await location_service.get_user_location(current_user.id, current_user.id)


@router.get("/history/{user_id}", response_model=List[LocationHistoryResponse])
async def get_location_history(
    user_id: int,
    start_time: Optional[datetime] = Query(None, description="Start time for history"),
    end_time: Optional[datetime] = Query(None, description="End time for history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of locations"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's location history if sharing is enabled."""
    location_service = LocationService(db)
    return await location_service.get_location_history(
        user_id, current_user.id, start_time, end_time, limit
    )


@router.get("/history", response_model=List[LocationHistoryResponse])
async def get_my_location_history(
    start_time: Optional[datetime] = Query(None, description="Start time for history"),
    end_time: Optional[datetime] = Query(None, description="End time for history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of locations"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's location history."""
    location_service = LocationService(db)
    return await location_service.get_location_history(
        current_user.id, current_user.id, start_time, end_time, limit
    )


@router.get("/nearby", response_model=List[NearbyUsersResponse])
async def find_nearby_users(
    radius_meters: int = Query(1000, ge=100, le=10000, description="Search radius in meters"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of users"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find nearby users within specified radius."""
    location_service = LocationService(db)
    return await location_service.find_nearby_users(current_user.id, radius_meters, limit)


@router.post("/shares", response_model=LocationShareResponse)
async def create_location_share(
    share_data: LocationShareCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new location share."""
    location_service = LocationService(db)
    return await location_service.create_location_share(current_user.id, share_data)


@router.get("/shares", response_model=List[LocationShareResponse])
async def get_location_shares(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all location shares for current user."""
    location_service = LocationService(db)
    return await location_service.get_user_location_shares(current_user.id)


@router.put("/shares/{share_id}", response_model=LocationShareResponse)
async def update_location_share(
    share_id: int,
    share_data: LocationShareUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a location share."""
    location_service = LocationService(db)
    updated_share = await location_service.update_location_share(
        share_id, current_user.id, share_data
    )
    if not updated_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location share not found"
        )
    return updated_share


@router.delete("/shares/{share_id}")
async def delete_location_share(
    share_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a location share."""
    location_service = LocationService(db)
    success = await location_service.delete_location_share(share_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location share not found"
        )
    return {"message": "Location share deleted successfully"}


@router.post("/geofences", response_model=GeofenceAreaResponse)
async def create_geofence_area(
    geofence_data: GeofenceAreaCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new geofence area."""
    location_service = LocationService(db)
    return await location_service.create_geofence_area(current_user.id, geofence_data)


@router.get("/geofences", response_model=List[GeofenceAreaResponse])
async def get_geofence_areas(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all geofence areas for current user."""
    location_service = LocationService(db)
    return await location_service.get_user_geofence_areas(current_user.id)


@router.put("/geofences/{geofence_id}", response_model=GeofenceAreaResponse)
async def update_geofence_area(
    geofence_id: int,
    geofence_data: GeofenceAreaUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a geofence area."""
    location_service = LocationService(db)
    updated_geofence = await location_service.update_geofence_area(
        geofence_id, current_user.id, geofence_data
    )
    if not updated_geofence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geofence area not found"
        )
    return updated_geofence


@router.delete("/geofences/{geofence_id}")
async def delete_geofence_area(
    geofence_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a geofence area."""
    location_service = LocationService(db)
    success = await location_service.delete_geofence_area(geofence_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geofence area not found"
        )
    return {"message": "Geofence area deleted successfully"}


@router.get("/geofences/events", response_model=List[GeofenceEventResponse])
async def get_geofence_events(
    geofence_id: Optional[int] = Query(None, description="Filter by geofence area ID"),
    start_time: Optional[datetime] = Query(None, description="Start time for events"),
    end_time: Optional[datetime] = Query(None, description="End time for events"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get geofence events for current user."""
    location_service = LocationService(db)
    return await location_service.get_geofence_events(
        current_user.id, geofence_id, start_time, end_time, limit
    )


@router.get("/stats", response_model=LocationStatsResponse)
async def get_location_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get location statistics for current user."""
    location_service = LocationService(db)
    return await location_service.get_location_stats(current_user.id, days)


# Admin endpoints (could be moved to a separate admin router)
@router.post("/admin/cleanup")
async def cleanup_old_location_data(
    days: int = Query(90, ge=30, le=365, description="Days to keep"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up old location data (admin only)."""
    # In a real application, you would check for admin privileges
    # For now, we'll allow any authenticated user
    location_service = LocationService(db)
    result = await location_service.cleanup_old_location_data(days)
    return {
        "message": "Cleanup completed",
        "deleted_records": result
    }
