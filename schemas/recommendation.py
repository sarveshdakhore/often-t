import uuid
from datetime import date
from typing import List, Optional, Dict, Any # Added Dict, Any
from pydantic import Field, validator
from .base import BaseSchema
from .itinerary import ItineraryRead # Reuse ItineraryRead for materialised result

# Added simple schema for destination info within the template
class DestinationInfo(BaseSchema):
    id: uuid.UUID
    name: str

class RecommendationRequest(BaseSchema):
    nights: int = Field(..., ge=1)
    start_date: date
    style: Optional[str] = None
    budget_min: Optional[float] = Field(None, ge=0, description="Minimum budget for the itinerary")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget for the itinerary")
    destination_id: Optional[uuid.UUID] = Field(None, description="Optional destination ID to filter templates") # Added destination_id

    @validator('budget_max')
    def check_budget_max_greater_than_min(cls, v, values, **kwargs):
        min_val = values.get('budget_min')
        if min_val is not None and v is not None and v < min_val:
            raise ValueError('budget_max must be greater than or equal to budget_min')
        return v

class TemplateDayRead(BaseSchema):
    id: uuid.UUID
    day_offset: int
    hotel_id: Optional[uuid.UUID] = None
    activity_id: Optional[uuid.UUID] = None
    transfer_id: Optional[uuid.UUID] = None
    # Potentially add nested Hotel/Activity/TransportMode info here

class TemplateRead(BaseSchema):
    id: uuid.UUID
    name: str
    nights: int
    style: Optional[str] = None
    budget: Optional[str] = None
    destinations: List[DestinationInfo] = [] # Changed to list of DestinationInfo
    avg_cost: Optional[float] = None
    template_days: List[TemplateDayRead] = []

# Response for GET /recommended-itineraries/ could be a TemplateRead
# or the fully materialised ItineraryRead depending on implementation choice.
# Let's assume it returns the materialised itinerary for now.
class RecommendationResponse(ItineraryRead):
    pass
