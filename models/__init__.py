# Make models easily accessible
from .base import Base, BaseModel
from .catalogue import Destination, Location, Hotel, Activity, TransportMode, TransportModeEnum
from .transactional import Itinerary, ItineraryDay, DayHotel, DayActivity, DayTransfer
from .recommendation import Template, TemplateDay

__all__ = [
    "Base",
    "BaseModel",
    "Destination",
    "Location",
    "Hotel",
    "Activity",
    "TransportMode",
    "TransportModeEnum",
    "Itinerary",
    "ItineraryDay",
    "DayHotel",
    "DayActivity",
    "DayTransfer",
    "Template",
    "TemplateDay",
]
