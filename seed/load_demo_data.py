import asyncio
import logging
from datetime import time
from uuid import uuid4
import random # Import random
import json # Import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust imports based on final project structure if needed
# Use relative imports since this script is inside the 'seed' package
from ..core.database import AsyncSessionLocal, engine, Base
from ..models import (
    Destination, Location, Hotel, Activity, TransportMode, TransportModeEnum,
    Template, TemplateDay
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants for Costs (INR) ---
# Rough estimates, adjust as needed
HOTEL_COSTS = {
    "Budget": (3000, 5000),
    "Mid-range": (6000, 10000),
    "Luxury": (15000, 30000),
}
ACTIVITY_COSTS = {
    "Adventure": (1500, 5000),
    "Culture": (500, 2000),
    "Relaxation": (1000, 4000),
    "Sightseeing": (200, 1500),
    "Beach": (0, 500), # Mostly free, maybe chair rental
    "Nightlife": (1000, 5000),
    "Shopping": (0, 10000), # Highly variable
}
TRANSFER_COSTS = {
    TransportModeEnum.TAXI: (500, 1500),
    TransportModeEnum.FERRY: (800, 2500),
    TransportModeEnum.PRIVATE_CAR: (1000, 3000),
    TransportModeEnum.MINIVAN: (1500, 4000),
    TransportModeEnum.BUS: (100, 500),
    TransportModeEnum.FLIGHT: (2000, 8000), # Domestic placeholder
}

def estimate_cost(min_val, max_val):
    """Estimate cost, favoring lower end slightly."""
    if min_val is None or max_val is None:
        return 0
    return random.uniform(min_val, min_val + (max_val - min_val) * 0.6) # Weighted towards min

async def seed_data(db: AsyncSession):
    """Seeds the database with demo data."""
    logger.info("Starting data seeding...")

    # --- Check if data exists ---
    result = await db.execute(select(Destination).limit(1))
    existing_destination = result.scalar_one_or_none()

    if existing_destination:
        logger.info("Destinations exist. Checking for templates...")
        result_template = await db.execute(select(Template).limit(1))
        if result_template.scalar_one_or_none():
            logger.info("Templates also exist. Skipping all seeding.")
            return
        else:
            logger.info("Destinations exist, but no templates. Seeding only templates...")
            # Fetch existing data needed for templates
            destinations = (await db.execute(select(Destination))).scalars().all()
            locations = (await db.execute(select(Location))).scalars().all()
            hotels = (await db.execute(select(Hotel))).scalars().all()
            activities = (await db.execute(select(Activity))).scalars().all()
            transport_modes = (await db.execute(select(TransportMode))).scalars().all()
            await seed_templates(db, destinations, locations, hotels, activities, transport_modes, phuket, krabi)
            await db.commit()
            logger.info("Template seeding completed.")
            return

    # --- Seed everything if no destinations found ---
    logger.info("No existing data found. Seeding all demo data...")

    # --- Destinations ---
    phuket = Destination(name="Phuket", latitude=7.9519, longitude=98.3364)
    krabi = Destination(name="Krabi", latitude=8.0863, longitude=98.9063)
    db.add_all([phuket, krabi])
    await db.flush() # Get IDs
    destinations = [phuket, krabi]
    logger.info("Seeded Destinations.")

    # --- Locations ---
    phuket_airport = Location(destination_id=phuket.id, name="Phuket International Airport (HKT)", kind="Airport")
    patong_beach_area = Location(destination_id=phuket.id, name="Patong Beach Area", kind="HotelArea")
    kata_beach_area = Location(destination_id=phuket.id, name="Kata Beach Area", kind="HotelArea")
    phi_phi_pier_phuket = Location(destination_id=phuket.id, name="Rassada Pier (Phi Phi Ferry)", kind="Pier")
    phuket_old_town = Location(destination_id=phuket.id, name="Phuket Old Town", kind="AttractionSite")
    big_buddha_phuket = Location(destination_id=phuket.id, name="Big Buddha Phuket", kind="AttractionSite")

    krabi_airport = Location(destination_id=krabi.id, name="Krabi International Airport (KBV)", kind="Airport")
    ao_nang_beach_area = Location(destination_id=krabi.id, name="Ao Nang Beach Area", kind="HotelArea")
    railay_beach = Location(destination_id=krabi.id, name="Railay Beach", kind="Beach") # Also HotelArea implicitly
    khao_ngon_nak = Location(destination_id=krabi.id, name="Khao Ngon Nak Viewpoint", kind="AttractionSite")
    phi_phi_pier_krabi = Location(destination_id=krabi.id, name="Klong Jilad Pier (Phi Phi Ferry)", kind="Pier")
    emerald_pool = Location(destination_id=krabi.id, name="Emerald Pool", kind="AttractionSite")

    locations_list = [
        phuket_airport, patong_beach_area, kata_beach_area, phi_phi_pier_phuket, phuket_old_town, big_buddha_phuket,
        krabi_airport, ao_nang_beach_area, railay_beach, khao_ngon_nak, phi_phi_pier_krabi, emerald_pool
    ]
    db.add_all(locations_list)
    await db.flush()
    locations = locations_list # Use the flushed list
    logger.info("Seeded Locations.")

    # --- Hotels ---
    # Phuket
    hotel_patong_budget = Hotel(location_id=patong_beach_area.id, name="Budget Hotel Patong", amenities={"pool": False, "wifi": True, "rating": 3, "price_category": "Budget"})
    hotel_patong_mid = Hotel(location_id=patong_beach_area.id, name="Mid-Range Resort Patong", amenities={"pool": True, "wifi": True, "rating": 4, "restaurant": True, "price_category": "Mid-range"})
    hotel_kata_luxury = Hotel(location_id=kata_beach_area.id, name="Luxury Kata Resort", amenities={"pool": True, "wifi": True, "rating": 5, "spa": True, "beachfront": True, "price_category": "Luxury"})
    hotel_kata_mid = Hotel(location_id=kata_beach_area.id, name="Kata Mid-Range Hotel", amenities={"pool": True, "wifi": True, "rating": 4, "price_category": "Mid-range"})
    # Krabi
    hotel_ao_nang_mid = Hotel(location_id=ao_nang_beach_area.id, name="Ao Nang Villa Resort", amenities={"pool": True, "wifi": True, "rating": 4, "beachfront": True, "price_category": "Mid-range"})
    hotel_railay_luxury = Hotel(location_id=railay_beach.id, name="Railay Bay Resort & Spa", amenities={"pool": True, "wifi": True, "rating": 4.5, "spa": True, "price_category": "Luxury"})
    hotel_ao_nang_budget = Hotel(location_id=ao_nang_beach_area.id, name="Ao Nang Budget Inn", amenities={"wifi": True, "rating": 3, "price_category": "Budget"})

    hotels_list = [
        hotel_patong_budget, hotel_patong_mid, hotel_kata_luxury, hotel_kata_mid,
        hotel_ao_nang_mid, hotel_railay_luxury, hotel_ao_nang_budget
    ]
    db.add_all(hotels_list)
    await db.flush()
    hotels = hotels_list
    logger.info("Seeded Hotels.")

    # --- Activities ---
    # Phuket
    activity_phi_phi_tour_pk = Activity(location_id=phi_phi_pier_phuket.id, name="Phi Phi Islands Day Tour (from Phuket)", category="Adventure", price_min=2500, price_max=4500, duration="Full Day")
    activity_old_town_walk_pk = Activity(location_id=phuket_old_town.id, name="Phuket Old Town Walking Tour", category="Culture", price_min=800, price_max=1500, duration="2-3 hours")
    activity_big_buddha_pk = Activity(location_id=big_buddha_phuket.id, name="Visit Big Buddha Phuket", category="Sightseeing", price_min=0, price_max=200, duration="1-2 hours") # Donation based
    activity_patong_beach_relax = Activity(location_id=patong_beach_area.id, name="Relax at Patong Beach", category="Beach", price_min=0, price_max=500, duration="Flexible")
    activity_kata_surf = Activity(location_id=kata_beach_area.id, name="Surfing Lesson at Kata Beach", category="Adventure", price_min=1000, price_max=2000, duration="1 hour")
    # Krabi
    activity_4_island_tour_kb = Activity(location_id=ao_nang_beach_area.id, name="Krabi 4 Islands Tour (from Ao Nang)", category="Adventure", price_min=1200, price_max=2000, duration="Half Day")
    activity_railay_climbing_kb = Activity(location_id=railay_beach.id, name="Rock Climbing Half-Day (Railay)", category="Adventure", price_min=1500, price_max=2500, duration="Half Day")
    activity_khao_ngon_nak_hike_kb = Activity(location_id=khao_ngon_nak.id, name="Hike to Khao Ngon Nak Viewpoint", category="Adventure", price_min=0, price_max=300, duration="3-4 hours") # Free, maybe guide/transport cost
    activity_emerald_pool_kb = Activity(location_id=emerald_pool.id, name="Visit Emerald Pool & Hot Springs", category="Relaxation", price_min=200, price_max=1000, duration="2-3 hours") # Entry fees + transport
    activity_ao_nang_relax = Activity(location_id=ao_nang_beach_area.id, name="Relax at Ao Nang Beach", category="Beach", price_min=0, price_max=500, duration="Flexible")

    activities_list = [
        activity_phi_phi_tour_pk, activity_old_town_walk_pk, activity_big_buddha_pk, activity_patong_beach_relax, activity_kata_surf,
        activity_4_island_tour_kb, activity_railay_climbing_kb, activity_khao_ngon_nak_hike_kb, activity_emerald_pool_kb, activity_ao_nang_relax
    ]
    db.add_all(activities_list)
    await db.flush()
    activities = activities_list
    logger.info("Seeded Activities.")

    # --- Transport Modes ---
    mode_ferry = TransportMode(code=TransportModeEnum.FERRY, name="Ferry")
    mode_taxi = TransportMode(code=TransportModeEnum.TAXI, name="Taxi / Grab")
    mode_private_car = TransportMode(code=TransportModeEnum.PRIVATE_CAR, name="Private Car / Longtail") # Combine for simplicity
    mode_minivan = TransportMode(code=TransportModeEnum.MINIVAN, name="Shared Minivan")
    mode_flight = TransportMode(code=TransportModeEnum.FLIGHT, name="Domestic Flight") # Added flight

    transport_modes_list = [mode_ferry, mode_taxi, mode_private_car, mode_minivan, mode_flight]
    db.add_all(transport_modes_list)
    await db.flush()
    transport_modes = transport_modes_list
    logger.info("Seeded Transport Modes.")

    # --- Seed Templates ---
    await seed_templates(db, destinations, locations, hotels, activities, transport_modes)

    await db.commit()
    logger.info("Data seeding completed successfully.")


async def seed_templates(db: AsyncSession, destinations, locations, hotels, activities, transport_modes, phuket, krabi):
    """Seeds ~20 diverse templates."""
    logger.info("Seeding templates...")

    styles = ["Adventure", "Relaxation", "Culture", "Family", "Luxury", "Budget", "Mixed"]
    budget_levels = ["Budget", "Mid-range", "Luxury"]
    num_templates_to_create = 20
    created_templates_count = 0

    # Get specific modes/locations for transfers
    mode_taxi = next((m for m in transport_modes if m.code == TransportModeEnum.TAXI), None)
    mode_ferry = next((m for m in transport_modes if m.code == TransportModeEnum.FERRY), None)
    phuket_airport = next((loc for loc in locations if loc.name == "Phuket International Airport (HKT)"), None)
    krabi_airport = next((loc for loc in locations if loc.name == "Krabi International Airport (KBV)"), None)
    phuket_pier = next((loc for loc in locations if loc.name == "Rassada Pier (Phi Phi Ferry)"), None)
    krabi_pier = next((loc for loc in locations if loc.name == "Klong Jilad Pier (Phi Phi Ferry)"), None)

    # Ensure essential modes/locations exist
    if not all([mode_taxi, mode_ferry, phuket_airport, krabi_airport, phuket_pier, krabi_pier]):
        logger.error("Essential transport modes or locations for transfers are missing. Aborting template seeding.")
        return

    while created_templates_count < num_templates_to_create:
        nights = random.randint(1, 8)
        style = random.choice(styles)
        budget_level = random.choice(budget_levels)

        # Determine primary destination and potentially secondary for multi-dest templates
        primary_destination = random.choice(destinations)
        involved_destinations = [primary_destination]
        # Simple logic: longer trips might involve a second destination
        if nights >= 4 and len(destinations) > 1 and random.random() < 0.4: # 40% chance for >=4 nights
            secondary_destination = random.choice([d for d in destinations if d.id != primary_destination.id])
            if secondary_destination:
                involved_destinations.append(secondary_destination)

        template_name = f"{primary_destination.name}{' & ' + secondary_destination.name if len(involved_destinations) > 1 else ''} {style} ({budget_level}) - {nights}N"
        # Avoid duplicate names if retrying
        existing_template_check = await db.execute(select(Template).where(Template.name == template_name))
        if existing_template_check.scalar_one_or_none():
            template_name += f" v{random.randint(1, 9)}" # Add suffix if name exists

        # Filter hotels/activities by *involved* destinations
        involved_dest_ids = {d.id for d in involved_destinations}
        dest_hotels = [h for h in hotels if h.location.destination_id in involved_dest_ids]
        dest_activities = [a for a in activities if a.location.destination_id in involved_dest_ids]

        if not dest_hotels or not dest_activities:
            logger.warning(f"Skipping template for {', '.join(d.name for d in involved_destinations)} due to missing hotels or activities.")
            continue # Skip if no hotels/activities for these destinations

        budget_hotels = [h for h in dest_hotels if h.amenities.get("price_category") == budget_level]
        if not budget_hotels: # Fallback to mid-range or any if specific budget level not found
            budget_hotels = [h for h in dest_hotels if h.amenities.get("price_category") == "Mid-range"] or dest_hotels

        # Prepare destinations JSONB data
        destinations_json = [{"id": str(d.id), "name": d.name} for d in involved_destinations]

        # Create Template record
        new_template = Template(
            name=template_name,
            nights=nights,
            style=style,
            budget=budget_level,
            destinations=destinations_json, # Store JSON list
            avg_cost=0 # Placeholder
        )
        db.add(new_template)
        await db.flush()

        template_days_data = []
        total_estimated_cost = 0
        current_hotel = None
        previous_hotel_location_id = None # Track location for transfers

        for day_offset in range(nights + 1): # 0 to nights (N+1 days)
            day_items = []
            day_cost = 0

            # --- Hotel Selection ---
            # Stay at the same hotel unless it's the first day or a change is triggered
            if day_offset == 0 or (day_offset > 0 and random.random() < 0.2): # ~20% chance to change hotel
                current_hotel = random.choice(budget_hotels)

            if day_offset < nights: # Only add hotel stay for nights 0 to N-1
                if current_hotel:
                    day_items.append(TemplateDay(
                        template_id=new_template.id,
                        day_offset=day_offset,
                        hotel_id=current_hotel.id
                    ))
                    hotel_cost_range = HOTEL_COSTS.get(current_hotel.amenities.get("price_category", "Mid-range"), HOTEL_COSTS["Mid-range"])
                    day_cost += estimate_cost(hotel_cost_range[0], hotel_cost_range[1])
                    current_hotel_location_id = current_hotel.location_id
                else: # Should not happen if budget_hotels is populated
                     logger.warning(f"No hotel selected for day {day_offset} in template {new_template.name}")
                     current_hotel_location_id = None
            else: # Last day (departure) - no hotel stay
                 current_hotel_location_id = None # No hotel on the last day

            # --- Activity Selection (for days 0 to N) ---
            if day_offset <= nights and current_hotel: # Add activities based on current hotel's location
                # Add 1-2 activities, less likely on first/last day
                num_activities = 0
                if 0 < day_offset < nights and random.random() < 0.8: # 80% chance on middle days
                    num_activities = random.randint(1, 2)
                elif (day_offset == 0 or day_offset == nights) and random.random() < 0.5: # 50% chance on first/last day
                    num_activities = 1

                location_activities = [a for a in dest_activities if a.location_id == current_hotel.location_id]
                if not location_activities: # Fallback: use any activity from the destination
                    location_activities = dest_activities

                if location_activities and num_activities > 0:
                    chosen_activities = random.sample(location_activities, min(num_activities, len(location_activities)))
                    for activity in chosen_activities:
                        day_items.append(TemplateDay(
                            template_id=new_template.id,
                            day_offset=day_offset,
                            activity_id=activity.id
                        ))
                        cost_range = ACTIVITY_COSTS.get(activity.category, (0, 1000)) # Default range
                        day_cost += estimate_cost(activity.price_min or cost_range[0], activity.price_max or cost_range[1])

            # --- Transfer Selection ---
            # Transfer *to* the current day's hotel location *from* the previous day's hotel location
            if day_offset > 0 and current_hotel_location_id and previous_hotel_location_id and current_hotel_location_id != previous_hotel_location_id:
                 # Simple transfer logic: use taxi between areas
                 day_items.append(TemplateDay(
                     template_id=new_template.id,
                     day_offset=day_offset, # Transfer happens *on* this day offset
                     transfer_id=mode_taxi.id
                 ))
                 cost_range = TRANSFER_COSTS.get(TransportModeEnum.TAXI)
                 day_cost += estimate_cost(cost_range[0], cost_range[1])
                 logger.debug(f"Added Taxi transfer for day {day_offset} in template {new_template.name}")

            # Add Ferry transfer between Phuket and Krabi (example on day 2 if applicable)
            # This requires more complex logic based on the sequence of destinations,
            # which isn't explicitly tracked here. Adding a placeholder rule:
            # If switching between Phuket hotel and Krabi hotel around day 2/3.
            is_pk_switch = False
            if current_hotel and previous_hotel_location_id:
                prev_dest_id = next((loc.destination_id for loc in locations if loc.id == previous_hotel_location_id), None)
                curr_dest_id = current_hotel.location.destination_id
                if prev_dest_id != curr_dest_id and {prev_dest_id, curr_dest_id} == {phuket.id, krabi.id}:
                     is_pk_switch = True

            if is_pk_switch and day_offset > 0:
                 # Remove the taxi transfer if added above for the same day
                 day_items = [item for item in day_items if not (item.day_offset == day_offset and item.transfer_id == mode_taxi.id)]
                 # Add ferry transfer
                 day_items.append(TemplateDay(
                     template_id=new_template.id,
                     day_offset=day_offset,
                     transfer_id=mode_ferry.id
                 ))
                 cost_range = TRANSFER_COSTS.get(TransportModeEnum.FERRY)
                 day_cost += estimate_cost(cost_range[0], cost_range[1])
                 logger.debug(f"Added Ferry transfer for day {day_offset} in template {new_template.name}")


            # Add items for the day and update total cost
            if day_items:
                template_days_data.extend(day_items)
            total_estimated_cost += day_cost

            # Update previous location for next iteration's transfer check
            previous_hotel_location_id = current_hotel_location_id if current_hotel else None


        # Add all TemplateDay objects for this template
        if template_days_data:
            db.add_all(template_days_data)

        # Update the template's average cost
        new_template.avg_cost = total_estimated_cost
        await db.flush() # Ensure cost is updated before commit

        created_templates_count += 1
        logger.info(f"Created template {created_templates_count}/{num_templates_to_create}: {new_template.name} (Est. Cost: {total_estimated_cost:.0f} INR)")

    logger.info(f"Finished seeding {created_templates_count} templates.")


async def main():
    logger.info("Initializing database...")
    # Ensure tables are created (optional, Alembic handles this usually)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_data(session)

    await engine.dispose()
    logger.info("Database connection closed.")

# ... existing __main__ block ...
if __name__ == "__main__":
    # Ensure event loop policy is set for Windows if needed
    # if sys.platform == "win32":
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
