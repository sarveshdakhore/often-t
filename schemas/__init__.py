from .base import BaseSchema
from .pagination import PaginationParams
from .itinerary import (
    ItineraryCreate,
    ItineraryRead,
    ItineraryList,
    PaginatedItineraryResponse,
    ItineraryDayCreate,
    ItineraryDayRead,
    DayHotelCreate,
    DayHotelRead,
    DayActivityCreate,
    DayActivityRead,
    DayTransferCreate,
    DayTransferRead,
)
from .recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    TemplateRead,
    TemplateDayRead,
)

__all__ = [
    "BaseSchema",
    "PaginationParams",
    "ItineraryCreate",
    "ItineraryRead",
    "ItineraryList",
    "PaginatedItineraryResponse",
    "ItineraryDayCreate",
    "ItineraryDayRead",
    "DayHotelCreate",
    "DayHotelRead",
    "DayActivityCreate",
    "DayActivityRead",
    "DayTransferCreate",
    "DayTransferRead",
    "RecommendationRequest",
    "RecommendationResponse",
    "TemplateRead",
    "TemplateDayRead",
]
