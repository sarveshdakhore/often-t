from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
from datetime import date

from api.deps import DbSession
from models.catalogue import Destination, Location, Activity
from schemas.catalogue import (
    LocationResponse,
    ActivityResponse,
    RecommendationRequest,
    RecommendationResponse
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalogue", tags=["catalogue"])

# Get all destinations
@router.get(
    "/destinations",
    response_model=List[dict],
    operation_id="get_destinations",
    summary="Get all destinations",
    description="Retrieves a list of all available destinations."
)
async def get_destinations(db: AsyncSession = Depends(DbSession)):
    """Get all available destinations"""
    result = await db.execute(select(Destination).where(Destination.is_active == True))
    destinations = result.scalars().all()
    return [{"id": dest.id, "name": dest.name} for dest in destinations]

# Get all locations for a destination
@router.get(
    "/destinations/{destination_id}/locations",
    response_model=List[LocationResponse],
    operation_id="get_locations_by_destination",
    summary="Get locations for a destination",
    description="Retrieves a list of locations for a specific destination."
)
async def get_locations_by_destination(
    destination_id: str,
    db: AsyncSession = Depends(DbSession)
):
    logger.info(f"Fetching locations for destination: {destination_id}")

    # First check if the destination exists
    result = await db.execute(select(Destination).where(Destination.id == destination_id))
    destination = result.scalar_one_or_none()
    if not destination:
        logger.warning(f"Destination {destination_id} not found")
        raise HTTPException(status_code=404, detail=f"Destination with ID {destination_id} not found")

    # Now get the locations
    result = await db.execute(select(Location).where(Location.destination_id == destination_id))
    locations = result.scalars().all()
    logger.info(f"Found {len(locations)} locations for destination {destination_id}")

    if not locations:
        # This is not an error - just an empty result
        return []

    return locations

# Get all activities for a location
@router.get(
    "/locations/{location_id}/activities",
    response_model=List[ActivityResponse],
    operation_id="get_activities_by_location",
    summary="Get activities for a location",
    description="Retrieves a list of activities for a specific location. Supports filtering by category."
)
async def get_activities_by_location(
    location_id: str,
    db: AsyncSession = Depends(DbSession),
    category: Optional[str] = None
):
    """
    Get activities for a specific location.
    If category is specified, filter by that category.
    If no category is specified, return all activities for the location.
    """
    # Check if location exists
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found")

    stmt = select(Activity).where(Activity.location_id == location_id)

    # Only apply category filter if it's specified
    if category:
        stmt = stmt.where(Activity.category == category)

    # Execute the query
    result = await db.execute(stmt)
    activities = result.scalars().all()

    if not activities:
        # Return empty array instead of 404
        return []

    return activities

# POST endpoint for recommended itineraries with optimized performance
@router.post(
    "/recommended-itineraries",
    response_model=RecommendationResponse,
    operation_id="recommend_itineraries",
    summary="Recommend itineraries",
    description="Generates recommended itineraries based on criteria such as number of nights, start date, styles, and activities."
)
async def recommend_itineraries(
    request: RecommendationRequest,
    db: DbSession
):
    """
    Get recommended itineraries based on multiple criteria:
    - Number of nights
    - Start date
    - Multiple styles (Adventure, Relaxation, Culture, etc.)
    - Multiple activities (optional)
    """
    logger.info(f"Generating recommendations for {request.nights} nights starting {request.start_date}")

    # Return placeholder until implemented
    return RecommendationResponse(
        message="Recommendation endpoint not fully implemented",
        itineraries=[]
    )

# GET endpoint for recommended itineraries (for backward compatibility)
@router.get(
    "/recommended-itineraries",
    response_model=RecommendationResponse,
    operation_id="get_recommended_itineraries",
    summary="Get recommended itineraries (Redirect)",
    description="Redirects to the POST endpoint logic for generating recommended itineraries based on query parameters."
)
async def get_recommended_itineraries(
    db: AsyncSession = Depends(DbSession),
    nights: int = Query(..., description="Number of nights"),
    start_date: date = Query(..., description="Start date in YYYY-MM-DD format"),
    style: str = Query(..., description="Travel style")
):
    """Redirects to the POST endpoint logic with single style parameter"""
    request = RecommendationRequest(
        nights=nights,
        start_date=start_date,
        styles=[style],
        activities=[]
    )
    return await recommend_itineraries(request, db)
