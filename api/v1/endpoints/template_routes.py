from fastapi import APIRouter, Depends, Query, HTTPException, status
from models import Template
from schemas import TemplateRead
from core.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
import uuid
from services.recommender import pick_template

router = APIRouter()

@router.get("/templates/recommend",
           response_model=List[TemplateRead],  # Using TemplateRead for now until TemplateDetailedRead is properly defined
           operation_id="get_template_recommendations",
           summary="Get template recommendations",
           description="Recommends templates based on nights, destination, and budget range")
async def get_template_recommendations(
    nights: Optional[int] = Query(5, ge=1, le=14, description="Number of nights for the trip"),
    destination_id: Optional[uuid.UUID] = Query(None, description="Filter by templates including this destination ID"),
    budget_min: Optional[float] = Query(None, ge=0, description="Minimum budget"),
    budget_max: Optional[float] = Query(None, ge=0, description="Maximum budget"),
    db: AsyncSession = Depends(get_db_session)
):
    """Recommend templates based on travel parameters"""
    try:
        # Get base template
        template = await pick_template(
            db=db,
            nights=nights,
            destination_id=destination_id,
            budget_min=budget_min,
            budget_max=budget_max
        )
        
        if not template:
            # Return empty list if no template found
            return []
        
        # For now, return basic template info - we'll enhance with detailed loading later
        return [TemplateRead.model_validate(template)]
    
    except Exception as e:
        # Log the error and return a helpful message
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in template recommendation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving template recommendations: {str(e)}"
        )