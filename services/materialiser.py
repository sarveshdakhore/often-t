import uuid
import logging
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Template, TemplateDay, Itinerary, ItineraryDay, DayHotel, DayActivity, DayTransfer, Location, TransportMode, Activity, Hotel # Added TemplateDay, Location, TransportMode, Activity, Hotel
from schemas import ItineraryRead # Use the read schema for the return type

logger = logging.getLogger(__name__)

async def materialise_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    start_date: date,
    traveler_name: Optional[str] = "Generated Itinerary",
    organisation_id: Optional[uuid.UUID] = None,
    meta: Optional[dict] = None,
) -> ItineraryRead:
    """
    Creates a concrete Itinerary instance from a Template.

    1. Fetches the Template and its TemplateDays.
    2. Creates an Itinerary record.
    3. Iterates through TemplateDays, creating corresponding ItineraryDay records
       and linking associated DayHotel, DayActivity, DayTransfer records.
    4. Wraps all database operations in a single transaction.
    5. Returns the fully populated ItineraryRead schema of the new itinerary.
    """
    logger.info(f"Materialising template {template_id} starting on {start_date}")

    # Fetch the template with its days eagerly loaded, including related entities
    stmt = (
        select(Template)
        .where(Template.id == template_id, Template.is_active == True)
        .options(
            selectinload(Template.template_days).selectinload(TemplateDay.hotel),
            selectinload(Template.template_days).selectinload(TemplateDay.activity),
            selectinload(Template.template_days).selectinload(TemplateDay.transfer_mode),
            # Eager load locations associated with hotels/activities if needed for transfers
            selectinload(Template.template_days).selectinload(TemplateDay.hotel).selectinload(Hotel.location),
            selectinload(Template.template_days).selectinload(TemplateDay.activity).selectinload(Activity.location),
        )
    )
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        logger.error(f"Template {template_id} not found or inactive.")
        raise ValueError(f"Template {template_id} not found or inactive.")

    new_itinerary_id = uuid.uuid4()
    new_itinerary = None

    async with db.begin(): # Start transaction
        # 1. Create Itinerary record
        new_itinerary = Itinerary(
            id=new_itinerary_id,
            traveler_name=traveler_name,
            start_date=start_date,
            nights=template.nights,
            organisation_id=organisation_id,
            meta=meta or {"template_id": str(template.id), "template_name": template.name},
        )
        db.add(new_itinerary)
        await db.flush() # Ensure itinerary ID is available

        # 2. Create ItineraryDay and related records
        day_map: dict[int, ItineraryDay] = {} # Store created days by offset
        location_map: dict[int, uuid.UUID] = {} # Store location ID for each day offset (based on hotel/activity)

        # Pre-process to determine locations for transfers
        for t_day in sorted(template.template_days, key=lambda d: d.day_offset):
             if t_day.hotel and t_day.hotel.location_id:
                 location_map[t_day.day_offset] = t_day.hotel.location_id
             elif t_day.activity and t_day.activity.location_id:
                 # Use activity location if hotel not present for the day
                 if t_day.day_offset not in location_map:
                     location_map[t_day.day_offset] = t_day.activity.location_id

        # Create days and link items
        for t_day in sorted(template.template_days, key=lambda d: d.day_offset):
            current_date = start_date + timedelta(days=t_day.day_offset)
            day_number = t_day.day_offset + 1

            # Create ItineraryDay if not already created for this offset
            if t_day.day_offset not in day_map:
                it_day = ItineraryDay(
                    itinerary_id=new_itinerary.id,
                    day_number=day_number,
                    date=current_date,
                )
                db.add(it_day)
                await db.flush() # Ensure day ID is available
                day_map[t_day.day_offset] = it_day
            else:
                it_day = day_map[t_day.day_offset]

            # Link Hotel if specified in template day
            if t_day.hotel_id:
                day_hotel = DayHotel(
                    itinerary_day_id=it_day.id,
                    hotel_id=t_day.hotel_id,
                    template=True # Set template flag
                    # check_in_time can be added later or defaulted
                )
                db.add(day_hotel)

            # Link Activity if specified
            if t_day.activity_id:
                day_activity = DayActivity(
                    itinerary_day_id=it_day.id,
                    activity_id=t_day.activity_id,
                    template=True # Set template flag
                    # timeslot can be added later or defaulted
                )
                db.add(day_activity)

            # Link Transfer if specified
            if t_day.transfer_id:
                 # Determine from/to locations based on previous/current day's location
                 from_offset = t_day.day_offset -1
                 to_offset = t_day.day_offset

                 from_loc_id = location_map.get(from_offset)
                 to_loc_id = location_map.get(to_offset)

                 if from_loc_id and to_loc_id:
                     day_transfer = DayTransfer(
                         itinerary_day_id=it_day.id, # Transfer happens *on* this day
                         mode_id=t_day.transfer_id,
                         from_location_id=from_loc_id,
                         to_location_id=to_loc_id,
                         template=True # Set template flag
                         # departure_time can be added later
                     )
                     db.add(day_transfer)
                     logger.info(f"Added transfer for day {day_number} from loc {from_loc_id} to loc {to_loc_id}")
                 else:
                     logger.warning(f"Could not determine from/to locations for transfer on day offset {t_day.day_offset}. From: {from_loc_id}, To: {to_loc_id}")


        # Ensure all days up to 'nights' are created, even if template doesn't specify activities/hotels
        for i in range(template.nights + 1): # 0 to nights (covers N+1 days)
             if i not in day_map:
                 current_date = start_date + timedelta(days=i)
                 day_number = i + 1
                 it_day = ItineraryDay(
                     itinerary_id=new_itinerary.id,
                     day_number=day_number,
                     date=current_date,
                 )
                 db.add(it_day)
                 day_map[i] = it_day


    # Transaction committed successfully if no exceptions occurred

    # Fetch the newly created itinerary with all relationships loaded for the response
    # Use the same query structure as the GET /itineraries/{id} endpoint
    stmt_read = (
        select(Itinerary)
        .where(Itinerary.id == new_itinerary_id)
        .options(
            selectinload(Itinerary.days)
            .selectinload(ItineraryDay.hotel_stay)
            .selectinload(DayHotel.hotel),
            selectinload(Itinerary.days)
            .selectinload(ItineraryDay.activities)
            .selectinload(DayActivity.activity),
            selectinload(Itinerary.days)
            .selectinload(ItineraryDay.transfers)
            .selectinload(DayTransfer.mode),
             selectinload(Itinerary.days)
            .selectinload(ItineraryDay.transfers)
            .selectinload(DayTransfer.from_location),
             selectinload(Itinerary.days)
            .selectinload(ItineraryDay.transfers)
            .selectinload(DayTransfer.to_location),
        )
        .order_by(ItineraryDay.day_number) # Ensure days are ordered
    )
    result_read = await db.execute(stmt_read)
    created_itinerary = result_read.scalar_one() # Should exist as transaction succeeded

    logger.info(f"Successfully materialised template {template_id} into itinerary {created_itinerary.id}")
    return ItineraryRead.model_validate(created_itinerary)
