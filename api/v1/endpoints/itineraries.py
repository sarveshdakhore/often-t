import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Response, Header, Body
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Annotated, Optional, Set

from api.deps import DbSession, PaginationDep
from models import Itinerary, ItineraryDay, DayHotel, DayActivity, DayTransfer, Location, Hotel, Activity, TransportMode
from schemas.itinerary import (
    ItineraryCreate, ItineraryRead, ItineraryReadWithDetails,
    ItineraryDayCreate, ItineraryDayRead,
    DayHotelCreate, DayHotelRead,
    DayActivityCreate, DayActivityRead,
    DayTransferCreate, DayTransferRead
)
from schemas import PaginatedItineraryResponse, ItineraryList
from services import itinerary_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Example data for request body
itinerary_create_example = {
    "traveler_name": "John Doe",
    "start_date": "2024-09-15",
    "nights": 1,
    "meta": {"purpose": "Vacation", "budget": 5000},
    "days": [
        {
            "day_number": 1,
            "date": "2024-09-15",
            "notes": "Arrival and check-in",
            "hotel_stay": {"hotel_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "check_in_time": "14:00:00"},
            "activities": [{"activity_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12", "timeslot": "Evening"}],
            "transfers": []
        },
        {
            "day_number": 2,
            "date": "2024-09-16",
            "notes": "Departure",
            "hotel_stay": None,
            "activities": [],
            "transfers": [{"mode_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13", "from_location_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15", "to_location_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14", "departure_time": "10:00:00"}]
        }
    ]
}

@router.post(
    "/",
    response_model=ItineraryReadWithDetails,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_itinerary",
    summary="Create a new Itinerary",
    description="Creates a complete itinerary including days, hotels, activities, and transfers.",
)
async def create_itinerary(
    session: DbSession,
    itinerary_in: ItineraryCreate = Body(..., example=itinerary_create_example)
):
    """
    Creates a new itinerary resource.
    """
    # Extract all entity IDs from the request for validation
    activity_ids: Set[uuid.UUID] = set()
    hotel_ids: Set[uuid.UUID] = set()
    mode_ids: Set[uuid.UUID] = set()
    location_ids: Set[uuid.UUID] = set()
    
    for day in itinerary_in.days:
        # Collect activity IDs
        for activity in day.activities:
            activity_ids.add(activity.activity_id)
            
        # Collect hotel IDs
        if day.hotel_stay and day.hotel_stay.hotel_id:
            hotel_ids.add(day.hotel_stay.hotel_id)
            
        # Collect transport mode and location IDs
        for transfer in day.transfers:
            mode_ids.add(transfer.mode_id)
            location_ids.add(transfer.from_location_id)
            location_ids.add(transfer.to_location_id)
    
    # Validate that all referenced activities exist - no transaction needed
    if activity_ids:
        activity_stmt = select(Activity.id).where(Activity.id.in_(activity_ids))
        result = await session.execute(activity_stmt)
        found_activity_ids = {id for (id,) in result}
        missing_activity_ids = activity_ids - found_activity_ids
        if missing_activity_ids:
            raise ValueError(f"Activities with IDs {', '.join(str(id) for id in missing_activity_ids)} not found")
    
    # Validate that all referenced hotels exist
    if hotel_ids:
        hotel_stmt = select(Hotel.id).where(Hotel.id.in_(hotel_ids))
        result = await session.execute(hotel_stmt)
        found_hotel_ids = {id for (id,) in result}
        missing_hotel_ids = hotel_ids - found_hotel_ids
        if missing_hotel_ids:
            raise ValueError(f"Hotels with IDs {', '.join(str(id) for id in missing_hotel_ids)} not found")
    
    # Validate that all referenced transport modes exist
    if mode_ids:
        mode_stmt = select(TransportMode.id).where(TransportMode.id.in_(mode_ids))
        result = await session.execute(mode_stmt)
        found_mode_ids = {id for (id,) in result}
        missing_mode_ids = mode_ids - found_mode_ids
        if missing_mode_ids:
            raise ValueError(f"Transport modes with IDs {', '.join(str(id) for id in missing_mode_ids)} not found")
    
    # Validate that all referenced locations exist
    if location_ids:
        location_stmt = select(Location.id).where(Location.id.in_(location_ids))
        result = await session.execute(location_stmt)
        found_location_ids = {id for (id,) in result}
        missing_location_ids = location_ids - found_location_ids
        if missing_location_ids:
            raise ValueError(f"Locations with IDs {', '.join(str(id) for id in missing_location_ids)} not found")
    
    # If validation passes (no exceptions), create the itinerary
    created_itinerary = await itinerary_service.create_itinerary_with_details(session, itinerary_in=itinerary_in)
    return created_itinerary


@router.get(
    "/{itinerary_id}",
    response_model=ItineraryRead,
    operation_id="get_itinerary_by_id",
    summary="Get Itinerary by ID",
    description="Retrieves the full details of a specific itinerary, including all days, activities, hotels, and transfers.",
)
async def get_itinerary(
    itinerary_id: uuid.UUID,
    db: DbSession,
    response: Response,
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
):
    """
    Fetches a single itinerary by its UUID, eager-loading related data.
    Includes basic ETag support (using updated_at).
    """
    logger.info(f"Fetching itinerary {itinerary_id}")
    stmt = (
        select(Itinerary)
        .where(Itinerary.id == itinerary_id, Itinerary.is_active == True)
        .options(
            selectinload(Itinerary.days.and_(ItineraryDay.is_active == True))
            .selectinload(ItineraryDay.hotel_stay)
            .selectinload(DayHotel.hotel).selectinload(Hotel.location),
            selectinload(Itinerary.days.and_(ItineraryDay.is_active == True))
            .selectinload(ItineraryDay.activities)
            .selectinload(DayActivity.activity).selectinload(Activity.location),
            selectinload(Itinerary.days.and_(ItineraryDay.is_active == True))
            .selectinload(ItineraryDay.transfers)
            .selectinload(DayTransfer.mode),
            selectinload(Itinerary.days.and_(ItineraryDay.is_active == True))
            .selectinload(ItineraryDay.transfers)
            .selectinload(DayTransfer.from_location),
            selectinload(Itinerary.days.and_(ItineraryDay.is_active == True))
            .selectinload(ItineraryDay.transfers)
            .selectinload(DayTransfer.to_location),
        )
    )
    result = await db.execute(stmt)
    itinerary = result.unique().scalar_one_or_none()

    if not itinerary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found")
    
    # Sort the days in Python after loading
    if itinerary.days:
        itinerary.days.sort(key=lambda day: day.day_number)

    # Basic ETag using updated_at timestamp
    etag = str(itinerary.updated_at.timestamp())
    response.headers["ETag"] = etag

    if if_none_match and if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    return ItineraryRead.model_validate(itinerary)


@router.get(
    "/",
    response_model=PaginatedItineraryResponse,
    operation_id="list_itineraries",
    summary="List Itineraries",
    description="Retrieves a paginated list of active itineraries (summary view).",
)
async def list_itineraries(
    db: DbSession,
    pagination: PaginationDep,
):
    """
    Fetches a paginated list of itineraries.
    """
    logger.info(f"Listing itineraries with limit={pagination.limit}, offset={pagination.offset}")

    # Count total active itineraries
    count_stmt = select(func.count(Itinerary.id)).where(Itinerary.is_active == True)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Fetch paginated itinerary summaries
    list_stmt = (
        select(Itinerary)
        .where(Itinerary.is_active == True)
        .order_by(Itinerary.created_at.desc())
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    result = await db.execute(list_stmt)
    itineraries = result.scalars().all()

    # Map to the list schema
    items = [ItineraryList.model_validate(it) for it in itineraries]

    return PaginatedItineraryResponse(
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        items=items,
    )

@router.delete(
    "/{itinerary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_itinerary",
    summary="Delete an Itinerary",
    description="Soft deletes an itinerary by setting is_active to False.",
)
async def delete_itinerary(
    itinerary_id: uuid.UUID,
    db: DbSession,
):
    """
    Soft deletes an itinerary by setting is_active to False.
    """
    logger.info(f"Soft deleting itinerary {itinerary_id}")
    
    # First check if the itinerary exists and is active
    check_stmt = select(Itinerary).where(Itinerary.id == itinerary_id, Itinerary.is_active == True)
    result = await db.execute(check_stmt)
    itinerary = result.scalar_one_or_none()
    
    if not itinerary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found or already deleted")
    
    # Perform soft delete
    itinerary.is_active = False
    await db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
