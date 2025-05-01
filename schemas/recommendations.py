from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Any
from uuid import UUID

class RecommendationRequest(BaseModel):
    nights: int = Field(..., ge=1, le=14, description="Number of nights")
    start_date: date = Field(..., description="Start date")
    styles: List[str] = Field(..., description="List of travel styles")
    activities: List[str] = Field(default=[], description="List of preferred activities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nights": 3,
                "start_date": "2025-05-10",
                "styles": ["Adventure", "Relaxation"],
                "activities": []
            }
        }

class RecommendationResponse(BaseModel):
    message: str
    itineraries: List[Any]  # Replace with proper itinerary type when defined
