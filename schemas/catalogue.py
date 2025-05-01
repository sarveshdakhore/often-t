from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Any
from datetime import date
from uuid import UUID
import uuid
from .base import BaseSchema
from models.catalogue import TransportModeEnum

class LocationBase(BaseModel):
    id: UUID
    name: str
    kind: str

class LocationResponse(LocationBase):
    class Config:
        orm_mode = True

class ActivityBase(BaseModel):
    id: UUID
    name: str
    category: str
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    duration: float = 12.0  # Default to 12 hours

class ActivityResponse(ActivityBase):
    class Config:
        orm_mode = True

class RecommendationRequest(BaseModel):
    nights: int = Field(..., description="Number of nights")
    start_date: date = Field(..., description="Start date")
    styles: List[str] = Field(..., description="List of travel styles")
    activities: List[UUID] = Field(default=[], description="Optional list of activity IDs")

class RecommendationResponse(BaseModel):
    message: str
    itineraries: List[dict]  # Simple dictionary structure without strict typing

# --- Destination ---
class DestinationRead(BaseSchema):
    id: uuid.UUID
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# --- Location ---
class LocationRead(BaseSchema):
    id: uuid.UUID
    destination_id: uuid.UUID
    name: str
    kind: Optional[str] = None # e.g., Airport, HotelArea, Pier, AttractionSite

# --- Hotel ---
class HotelRead(BaseSchema):
    id: uuid.UUID
    location_id: uuid.UUID
    name: str
    amenities: Optional[Dict[str, Any]] = None # JSONB field

# --- Activity ---
class ActivityRead(BaseSchema):
    id: uuid.UUID
    location_id: uuid.UUID
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    duration: Optional[str] = None

# --- Transport Mode ---
class TransportModeRead(BaseSchema):
    id: uuid.UUID
    code: TransportModeEnum # Use the enum directly
    name: str

# --- Schemas used by MCP (can be removed or kept separate if preferred) ---
class LocationResponse(LocationRead): # Example alias if used elsewhere
    pass

class ActivityResponse(ActivityRead): # Example alias if used elsewhere
    pass

class HotelResponse(HotelRead): # Example alias if used elsewhere
    pass
