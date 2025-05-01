import logging
from fastapi import APIRouter, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy import select
from datetime import date as dt_date, datetime, time, timedelta
from pydantic import BaseModel, Field
import json

from api.deps import DbSession
from models.recommendation import Template, TemplateDay
from models.catalogue import Hotel, Activity as ActivityModel, Location, TransportMode
from models.transactional import DayHotel, DayActivity, DayTransfer
from services.recommender import pick_template

router = APIRouter(tags=["recommendations"])
logger = logging.getLogger(__name__)

# Pydantic models for documentation
class HotelStay(BaseModel):
    hotel_id: str = Field(..., description="UUID of the hotel")
    check_in_time: str = Field(..., description="Check-in time in format HH:MM:SS")

class ActivitySchema(BaseModel):
    activity_id: str = Field(..., description="UUID of the activity")
    timeslot: str = Field(..., description="Time slot (Morning, Afternoon, Evening)")

class Transfer(BaseModel):
    mode_id: str = Field(..., description="UUID of the transportation mode")
    from_location_id: str = Field(..., description="UUID of the departure location")
    to_location_id: str = Field(..., description="UUID of the destination location")
    departure_time: str = Field(..., description="Departure time in format HH:MM:SS")

class DayItinerary(BaseModel):
    day_number: int = Field(..., description="Sequential day number (1, 2, 3...)")
    date: dt_date = Field(..., description="Date in format YYYY-MM-DD")
    notes: Optional[str] = Field(None, description="Additional notes for this day")
    hotel_stay: Optional[HotelStay] = Field(None, description="Hotel details if staying overnight")
    activities: List[ActivitySchema] = Field(default_factory=list, description="List of activities for this day")
    transfers: List[Transfer] = Field(default_factory=list, description="List of transfers for this day")

class ItineraryMeta(BaseModel):
    purpose: str = Field(..., description="Purpose of travel (Business, Vacation, etc.)")
    budget: float = Field(..., description="Budget in relevant currency")

class TravelItinerary(BaseModel):
    traveler_name: str = Field(..., description="Name of the traveler")
    start_date: dt_date = Field(..., description="Start date in format YYYY-MM-DD")
    nights: int = Field(..., ge=1, description="Number of nights")
    meta: ItineraryMeta = Field(..., description="Additional metadata")
    days: List[DayItinerary] = Field(..., description="Daily itinerary details")

class ItineraryDataRequest(BaseModel):
    """Request body for converting itinerary data to proper JSON string"""
    data: Dict[str, Any] = Field(..., description="Itinerary data as dictionary")
    for_claude: bool = Field(False, description="Format response specifically for Claude consumption")

@router.post(
    "/format-itinerary-json",
    response_model=Dict[str, Any],
    operation_id="format_itinerary_json", 
    summary="Format Itinerary as JSON String",
    description="Converts an itinerary data dictionary to a properly formatted JSON string for use with MCP tools",
)
async def format_itinerary_json(
    request: ItineraryDataRequest = Body(...)
):
    """
    Converts an itinerary data dictionary to a properly formatted JSON string.
    This ensures the JSON string is properly formatted for MCP tools that expect string input.
    """
    try:
        # Convert the data to a JSON string
        json_string = json.dumps(request.data)
        
        # If the response is for Claude, add usage examples
        if request.for_claude:
            return {
                "json_string": json_string,
                "usage_example": f"To create this itinerary, use:\n\n```python\nresult = await create_custom_itinerary('{json_string}')\n```",
                "note": "The JSON string above is already properly formatted and can be passed directly to the create_custom_itinerary tool."
            }
        else:
            return {"json_string": json_string}
            
    except Exception as e:
        logger.error(f"Error formatting itinerary JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error formatting JSON: {str(e)}"
        )

@router.get(
    "/templates-by-nights",
    response_model=Dict[str, Any],
    operation_id="get_templates_by_nights",
    summary="Get Templates by Nights",
    description="Gets templates matching the specified number of nights with all related data in itinerary format",
)
async def get_templates_by_nights(
    nights: int = Query(..., ge=1, description="Number of nights for the templates"),
    start_date_str: Optional[str] = Query(None, description="Optional start date in YYYY-MM-DD format"),
    db: DbSession = None
):
    """
    Get templates by number of nights and convert to itinerary format.
    Returns a complete itinerary structure based on the template data.
    """
    try:
        # Parse start date or use today
        try:
            start_date = dt_date.fromisoformat(start_date_str) if start_date_str else dt_date.today()
        except ValueError:
            start_date = dt_date.today()
            logger.warning(f"Invalid start date format: {start_date_str}, using today instead")

        # Find a suitable template based on nights
        template = await pick_template(
            db=db,
            nights=nights,
            destination_id=None,
            budget_min=None,
            budget_max=None
        )
        
        if not template:
            logger.info(f"No templates found for {nights} nights")
            return {}
        
        # Get the template 
        template_query = select(Template).where(Template.id == template.id)
        result = await db.execute(template_query)
        template = result.scalar_one_or_none()
        
        if not template:
            return {}
        
        # Create the itinerary structure
        itinerary_id = uuid.uuid4()
        current_timestamp = datetime.utcnow().isoformat() + "Z"
        
        itinerary = {
            "id": str(itinerary_id),
            "traveler_name": f"Template: {template.name}",
            "start_date": start_date.isoformat(),
            "nights": template.nights,
            "organisation_id": None,
            "meta": {
                "budget": template.avg_cost or 5000,
                "purpose": "Vacation",
                "template_id": str(template.id),
                "template_name": template.name,
                "template_style": template.style,
            },
            "days": [],
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
            "is_active": True
        }
        
        # Get all template days
        days_query = select(TemplateDay).where(TemplateDay.template_id == template.id)
        days_result = await db.execute(days_query)
        template_days = days_result.scalars().all()
        
        # Create data maps for efficient lookups
        # 1. Get all hotel data
        hotel_ids = [day.hotel_id for day in template_days if day.hotel_id is not None]
        hotel_map = {}
        hotel_location_map = {}
        if hotel_ids:
            hotels_query = select(Hotel).where(Hotel.id.in_(hotel_ids))
            hotels_result = await db.execute(hotels_query)
            hotels = hotels_result.scalars().all()
            hotel_map = {hotel.id: hotel for hotel in hotels}
            
            # Get all locations for hotels
            location_ids = [hotel.location_id for hotel in hotels]
            locations_query = select(Location).where(Location.id.in_(location_ids))
            locations_result = await db.execute(locations_query)
            locations = locations_result.scalars().all()
            location_map = {location.id: location for location in locations}
            
            # Link hotels to their locations
            for hotel_id, hotel in hotel_map.items():
                hotel_location_map[hotel_id] = location_map.get(hotel.location_id)
        
        # 2. Get all activity data
        activity_ids = [day.activity_id for day in template_days if day.activity_id is not None]
        activity_map = {}
        if activity_ids:
            activities_query = select(ActivityModel).where(ActivityModel.id.in_(activity_ids))
            activities_result = await db.execute(activities_query)
            activities = activities_result.scalars().all()
            activity_map = {activity.id: activity for activity in activities}
        
        # 3. Get all transport mode data
        transport_ids = [day.transfer_id for day in template_days if day.transfer_id is not None]
        transport_map = {}
        if transport_ids:
            transport_query = select(TransportMode).where(TransportMode.id.in_(transport_ids))
            transport_result = await db.execute(transport_query)
            transport_modes = transport_result.scalars().all()
            transport_map = {mode.id: mode for mode in transport_modes}
        
        # Process days and build itinerary structure
        day_offset_map = {}
        for day in sorted(template_days, key=lambda x: x.day_offset):
            day_offset = day.day_offset
            day_number = day_offset + 1  # Convert from 0-based to 1-based
            
            # Create the day if not already created
            if day_offset not in day_offset_map:
                day_date = start_date + timedelta(days=day_offset)
                itinerary_day = {
                    "id": str(uuid.uuid4()),
                    "day_number": day_number,
                    "date": day_date.isoformat(),
                    "notes": f"Day {day_number} of your trip",
                    "hotel_stay": None,
                    "activities": [],
                    "transfers": [],
                    "created_at": current_timestamp,
                    "updated_at": current_timestamp
                }
                day_offset_map[day_offset] = itinerary_day
                itinerary["days"].append(itinerary_day)
            else:
                itinerary_day = day_offset_map[day_offset]
                
            # Add hotel stay if available and not already added
            if day.hotel_id and not itinerary_day["hotel_stay"] and day.hotel_id in hotel_map:
                hotel = hotel_map[day.hotel_id]
                itinerary_day["hotel_stay"] = {
                    "id": str(uuid.uuid4()),
                    "hotel_id": str(hotel.id),
                    "check_in_time": "14:00:00"  # Default check-in time
                }
                
            # Add activity if available
            if day.activity_id and day.activity_id in activity_map:
                activity = activity_map[day.activity_id]
                itinerary_day["activities"].append({
                    "id": str(uuid.uuid4()),
                    "activity_id": str(activity.id),
                    "timeslot": "Morning" if len(itinerary_day["activities"]) == 0 else 
                               "Afternoon" if len(itinerary_day["activities"]) == 1 else "Evening",
                })
                
            # Add transfer if available
            if day.transfer_id and day.transfer_id in transport_map:
                # Find previous day for from_location
                prev_day = None
                for td in template_days:
                    if td.day_offset == day_offset - 1 and td.hotel_id:
                        prev_day = td
                        break
                
                # Only add transfer if we have both from and to locations
                if prev_day and prev_day.hotel_id and day.hotel_id:
                    prev_hotel = hotel_map.get(prev_day.hotel_id)
                    curr_hotel = hotel_map.get(day.hotel_id)
                    
                    if prev_hotel and curr_hotel:
                        from_location = location_map.get(prev_hotel.location_id)
                        to_location = location_map.get(curr_hotel.location_id)
                        
                        if from_location and to_location:
                            itinerary_day["transfers"].append({
                                "id": str(uuid.uuid4()),
                                "mode_id": str(day.transfer_id),
                                "from_location_id": str(from_location.id),
                                "to_location_id": str(to_location.id),
                                "departure_time": "09:00:00"  # Default departure time
                            })
        
        # Make sure days are correctly ordered
        itinerary["days"] = sorted(itinerary["days"], key=lambda x: x["day_number"])
        
        return itinerary
        
    except Exception as e:
        logger.error(f"Error fetching template by nights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching template: {str(e)}"
        )
