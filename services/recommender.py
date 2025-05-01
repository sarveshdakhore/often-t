import logging
from typing import Optional
from sqlalchemy import select, asc, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from models import Template

logger = logging.getLogger(__name__)

async def pick_template(
    db: AsyncSession,
    nights: int,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    destination_id: Optional[uuid.UUID] = None,
) -> Optional[Template]:
    """
    V1 Rule-based recommender: Picks the best template based on criteria.
    Filters by nights, destination (checks if destination_id is in the 'destinations' JSONB list),
    and budget range (avg_cost, optional).
    Ranks by average cost (asc).
    Returns the top-ranked template or None.
    """
    logger.info(f"Picking template V1 for nights={nights}, destination={destination_id}, budget_min={budget_min}, budget_max={budget_max}")

    stmt = select(Template).where(Template.nights == nights, Template.is_active == True)

    # Filter by destination if provided using JSONB containment
    if destination_id:
        # Construct the JSON object to check for containment
        # Check if the list contains an object like {"id": "uuid_string"}
        destination_filter = json.dumps([{"id": str(destination_id)}])
        # Cast the filter string to JSONB for the query and use the contains operator (@>)
        stmt = stmt.where(Template.destinations.cast(JSONB).contains(cast(destination_filter, JSONB)))

    # Filter by budget range using avg_cost
    if budget_min is not None:
        stmt = stmt.where(Template.avg_cost >= budget_min)
    if budget_max is not None:
        stmt = stmt.where(Template.avg_cost <= budget_max)

    # Ranking: Cost low
    stmt = stmt.order_by(asc(Template.avg_cost))

    result = await db.execute(stmt.limit(1))
    template = result.scalar_one_or_none()

    if template:
        logger.info(f"Found matching template: {template.id} ({template.name}) involving destination {destination_id} with avg_cost: {template.avg_cost}")
    else:
        logger.warning(f"No matching template found for nights={nights}, destination={destination_id}, budget=({budget_min}-{budget_max}).")

    return template
