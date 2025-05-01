import uuid
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any
from pydantic import Field
from .base import BaseSchema

# --- Nested Schemas ---

class DayHotelBase(BaseSchema):
    hotel_id: uuid.UUID
    check_in_time: Optional[time] = None

class DayHotelCreate(DayHotelBase):
    pass

class DayHotelRead(DayHotelBase):
    id: uuid.UUID
    # Add hotel details if needed, e.g., hotel_name: str

class DayActivityBase(BaseSchema):
    activity_id: uuid.UUID
    timeslot: Optional[str] = None

class DayActivityCreate(DayActivityBase):
    pass

class DayActivityRead(DayActivityBase):
    id: uuid.UUID
    # Add activity details if needed

class DayTransferBase(BaseSchema):
    mode_id: uuid.UUID
    from_location_id: uuid.UUID
    to_location_id: uuid.UUID
    departure_time: Optional[time] = None

class DayTransferCreate(DayTransferBase):
    pass

class DayTransferRead(DayTransferBase):
    id: uuid.UUID
    # Add mode/location details if needed

class ItineraryDayBase(BaseSchema):
    day_number: int = Field(..., ge=1)
    date: date
    notes: Optional[str] = None # Added notes field based on example
    hotel_stay: Optional[DayHotelCreate] = None
    activities: List[DayActivityCreate] = []
    transfers: List[DayTransferCreate] = []

class ItineraryDayCreate(ItineraryDayBase):
    pass # Input structure for creating a day

class ItineraryDayRead(ItineraryDayBase):
    id: uuid.UUID
    hotel_stay: Optional[DayHotelRead] = None
    activities: List[DayActivityRead] = []
    transfers: List[DayTransferRead] = []
    created_at: datetime
    updated_at: datetime

# --- Main Itinerary Schemas ---

class ItineraryBase(BaseSchema):
    traveler_name: Optional[str] = None
    start_date: date
    nights: int = Field(..., ge=1)
    organisation_id: Optional[uuid.UUID] = None
    meta: Optional[Dict[str, Any]] = None

class ItineraryCreate(ItineraryBase):
    # Allow creating days directly with the itinerary
    days: List[ItineraryDayCreate] = []
    
class ItineraryCreateLOL(ItineraryBase):
    # Allow creating days directly with the itinerary
    days: List[ItineraryDayCreate] = []

class ItineraryRead(ItineraryBase):
    id: uuid.UUID
    days: List[ItineraryDayRead] = [] # Include full day details on read
    created_at: datetime
    updated_at: datetime
    is_active: bool

# Define ItineraryReadWithDetails (can be same as ItineraryRead for now)
# If you need different fields later, adjust this definition.
ItineraryReadWithDetails = ItineraryRead

class ItineraryList(BaseSchema):
    """Schema for listing multiple itineraries (summary)."""
    id: uuid.UUID
    traveler_name: Optional[str] = None
    start_date: date
    nights: int
    created_at: datetime

class PaginatedItineraryResponse(BaseSchema):
    total: int
    limit: int
    offset: int
    items: List[ItineraryList]
