import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import DbSession # Use your dependency injection function
from models import Destination, Location, Activity, Hotel, TransportMode
from schemas.catalogue import ( # Import the new Read schemas
    DestinationRead, LocationRead, ActivityRead, HotelRead, TransportModeRead
)

# Remove the prefix from the router so it can be properly mounted in the main app
router = APIRouter(tags=["catalogue"])
logger = logging.getLogger(__name__)

@router.get("/destinations", response_model=List[DestinationRead])
async def get_destinations(db: DbSession):
    """Retrieve all active destinations."""
    result = await db.execute(select(Destination).where(Destination.is_active == True))
    return result.scalars().all()

@router.get("/destinations/{destination_id}/locations", response_model=List[LocationRead])
async def get_locations_by_destination(destination_id: uuid.UUID, db: DbSession):
    """Retrieve active locations for a specific destination."""
    # Optional: Check if destination exists first
    dest_check = await db.get(Destination, destination_id)
    if not dest_check or not dest_check.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")

    result = await db.execute(
        select(Location)
        .where(Location.destination_id == destination_id, Location.is_active == True)
    )
    return result.scalars().all()

@router.get("/locations/{location_id}/activities", response_model=List[ActivityRead])
async def get_activities_by_location(
    location_id: uuid.UUID,
    db: DbSession,
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Retrieve active activities for a specific location, optionally filtered by category."""
    # Optional: Check if location exists first
    loc_check = await db.get(Location, location_id)
    if not loc_check or not loc_check.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    stmt = select(Activity).where(Activity.location_id == location_id, Activity.is_active == True)
    if category:
        stmt = stmt.where(Activity.category == category)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/locations/{location_id}/hotels", response_model=List[HotelRead])
async def get_hotels_by_location(location_id: uuid.UUID, db: DbSession):
    """Retrieve active hotels for a specific location."""
    # Optional: Check if location exists first
    loc_check = await db.get(Location, location_id)
    if not loc_check or not loc_check.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    result = await db.execute(
        select(Hotel)
        .where(Hotel.location_id == location_id, Hotel.is_active == True)
    )
    return result.scalars().all()

@router.get("/transport-modes", response_model=List[TransportModeRead])
async def get_transport_modes(db: DbSession):
    """Retrieve all active transport modes."""
    result = await db.execute(select(TransportMode).where(TransportMode.is_active == True))
    return result.scalars().all()

