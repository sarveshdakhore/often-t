"""
Service-layer helper that inserts an itinerary plus nested days / hotels /
activities / transfers in ONE transaction.  The AsyncSession is supplied by
FastAPI's dependency – don't start another transaction here.
"""
from __future__ import annotations

import uuid
import logging
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import (
    Itinerary,
    ItineraryDay,
    DayHotel,
    DayActivity,
    DayTransfer,
    Hotel,
    Activity,
    Location,
)
from schemas.itinerary import ItineraryCreate, ItineraryReadWithDetails

logger = logging.getLogger(__name__)

async def create_itinerary_with_details(
    session: AsyncSession,
    itinerary_in: ItineraryCreate,
) -> ItineraryReadWithDetails:
    # 1 — parent row
    itinerary = Itinerary(
        id=uuid.uuid4(),
        traveler_name=itinerary_in.traveler_name,
        start_date=itinerary_in.start_date,
        nights=itinerary_in.nights,
        meta=itinerary_in.meta,
    )
    session.add(itinerary)
    await session.flush()             # get PK now

    # 2 — children
    for day_in in itinerary_in.days:
        day = ItineraryDay(
            itinerary_id=itinerary.id,
            day_number=day_in.day_number,
            date=day_in.date,
            notes=day_in.notes,
        )
        session.add(day)
        await session.flush()

        # optional hotel
        if day_in.hotel_stay:
            session.add(
                DayHotel(
                    itinerary_day_id=day.id,
                    hotel_id=day_in.hotel_stay.hotel_id,
                    check_in_time=day_in.hotel_stay.check_in_time,
                )
            )

        # zero-plus activities
        for a in day_in.activities:
            session.add(
                DayActivity(
                    itinerary_day_id=day.id,
                    activity_id=a.activity_id,
                    timeslot=a.timeslot,
                )
            )

        # zero-plus transfers
        for t in day_in.transfers:
            session.add(
                DayTransfer(
                    itinerary_day_id=day.id,
                    mode_id=t.mode_id,
                    from_location_id=t.from_location_id,
                    to_location_id=t.to_location_id,
                    departure_time=t.departure_time,
                )
            )

    # Fetch the full itinerary with relationships for the response
    stmt = (
        select(Itinerary)
        .options(
            selectinload(Itinerary.days),
            selectinload(Itinerary.days).selectinload(ItineraryDay.hotel_stay),
            selectinload(Itinerary.days).selectinload(ItineraryDay.activities),
            selectinload(Itinerary.days).selectinload(ItineraryDay.transfers),
        )
        .where(Itinerary.id == itinerary.id)
    )
    result = await session.execute(stmt)
    created_itinerary = result.unique().scalar_one()

    # Sort days by day_number
    if created_itinerary.days:
        created_itinerary.days.sort(key=lambda day: day.day_number)

    # ← commit happens in the dependency
    return ItineraryReadWithDetails.model_validate(created_itinerary)
