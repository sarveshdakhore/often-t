from typing import Any, Dict, List, Optional
from datetime import time
import uuid
from pydantic import BaseModel as BaseSchema

class TemplateDetailedRead(BaseSchema):
    """Template schema with detailed related entities (days, hotels, activities, transfers)"""
    id: uuid.UUID
    name: str
    nights: int
    style: Optional[str] = None
    budget: Optional[str] = None
    popularity: Optional[float] = None
    avg_cost: Optional[float] = None
    destinations: Optional[Dict[str, Any]] = None  # JSONB field
    days: List["TemplateDayWithRelatedData"]
    
    class Config:
        orm_mode = True

class HotelInTemplate(BaseSchema):
    """Hotel summary in template context"""
    id: uuid.UUID
    name: str
    location_id: uuid.UUID
    amenities: Optional[Dict[str, Any]] = None

class ActivityInTemplate(BaseSchema):
    """Activity summary in template context"""
    id: uuid.UUID  
    name: str
    location_id: uuid.UUID
    category: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    duration: Optional[str] = None

class TransferInTemplate(BaseSchema):
    """Transfer summary in template context"""
    id: uuid.UUID
    mode_id: uuid.UUID
    mode_name: str
    from_location_id: uuid.UUID
    to_location_id: uuid.UUID
    departure_time: Optional[time] = None

class TemplateDayWithRelatedData(BaseSchema):
    """Template day with all related data"""
    id: uuid.UUID
    day_number: int
    hotel_id: Optional[uuid.UUID] = None
    hotel: Optional[HotelInTemplate] = None
    activities: List[ActivityInTemplate] = []
    transfers: List[TransferInTemplate] = []

# Make sure to update Pydantic references
TemplateDayWithRelatedData.update_forward_refs()
TemplateDetailedRead.update_forward_refs()