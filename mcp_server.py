from typing import Any, Optional, List, Dict
import httpx
from mcp.server.fastmcp import FastMCP
import uuid
from datetime import date, time
import logging
import json

from sqlalchemy import select
from schemas.itinerary import ItineraryCreate, ItineraryReadWithDetails, ItineraryRead
from schemas.catalogue import LocationResponse, ActivityResponse, HotelResponse
from models import Destination, Location, Activity, Hotel, TransportMode
from services.recommender import pick_template
from core.database import get_db_session
from services.materialiser import materialise_template

mcp = FastMCP("often")
logger = logging.getLogger(__name__)


@mcp.tool()
async def get_destinations() -> List[Dict[str, Any]]:
    """
    Retrieves a list of all available travel destinations. Use this tool first to find the correct Destination and its ID for planning, especially when starting from scratch.

    This tool requires no parameters.

    Returns:
        A list of dictionaries, each representing a destination with its 'id' (UUID string) and 'name'.
        Example: [{"id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a10", "name": "Phuket"}]
    """
    logger.info("MCP: Fetching all destinations")
    async for session in get_db_session():
        try:
            result = await session.execute(select(Destination).where(Destination.is_active == True))
            destinations = result.scalars().all()
            return [{"id": str(dest.id), "name": dest.name} for dest in destinations]
        except Exception as e:
            logger.error(f"MCP: Error fetching destinations: {e}", exc_info=True)
            raise ValueError(f"Failed to fetch destinations: {e}")

@mcp.tool()
async def get_locations_by_destination(destination_id_str: str) -> List[Dict[str, Any]]:
    """
    Retrieves specific locations within a given destination, using the Destination ID obtained from `get_destinations`.
    Locations include airports, hotel areas, piers, attraction sites, etc. Use this to find Location IDs needed for hotels, activities, and transfers.

    Args:
        destination_id_str: The unique identifier (UUID string) of the destination.

    Returns:
        A list of dictionaries, each representing a location with its 'id' (UUID string), 'name', and 'kind'.
        Example: [{"id": "121fc980-993d-44aa-bb6d-9eb1a356034b", "name": "Patong Beach Area", "kind": "HotelArea"}]
    """
    logger.info(f"MCP: Fetching locations for destination_id: {destination_id_str}")
    try:
        destination_id = uuid.UUID(destination_id_str)
    except ValueError:
        logger.error(f"MCP: Invalid destination_id format: {destination_id_str}")
        raise ValueError("Invalid destination_id format. It must be a valid UUID.")

    async for session in get_db_session():
        try:
            dest_check = await session.get(Destination, destination_id)
            if not dest_check or not dest_check.is_active:
                logger.warning(f"MCP: Destination not found or inactive: {destination_id_str}")
                return []

            result = await session.execute(
                select(Location)
                .where(Location.destination_id == destination_id, Location.is_active == True)
            )
            locations = result.scalars().all()
            return [
                {"id": str(loc.id), "name": loc.name, "kind": loc.kind}
                for loc in locations
            ]
        except Exception as e:
            logger.error(f"MCP: Error fetching locations for destination {destination_id_str}: {e}", exc_info=True)
            raise ValueError(f"Failed to fetch locations: {e}")

@mcp.tool()
async def get_activities_by_location(location_id_str: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves activities available at a specific location, using the Location ID obtained from `get_locations_by_destination`.

    Args:
        location_id_str: The unique identifier (UUID string) of the location.
        category: Optional. Filter activities by category (e.g., 'Adventure', 'Culture').

    Returns:
        A list of dictionaries, each representing an activity with its full details: 'id', 'name', 'category', 'price_min', 'price_max', 'duration', and 'location_id'. Use the 'id' from this list when adding activities to a custom itinerary.
        Example: [{"id": "76cbbe15-1117-46b2-8af2-8571a65ccec8", "name": "Phi Phi Islands Day Tour", "category": "Adventure", "price_min": 2500, "price_max": 4500, "duration": "Full Day", "location_id": "..."}]
    """
    logger.info(f"MCP: Fetching activities for location_id: {location_id_str}, category: {category}")
    try:
        location_id = uuid.UUID(location_id_str)
    except ValueError:
        logger.error(f"MCP: Invalid location_id format: {location_id_str}")
        raise ValueError("Invalid location_id format. It must be a valid UUID.")

    async for session in get_db_session():
        try:
            loc_check = await session.get(Location, location_id)
            if not loc_check or not loc_check.is_active:
                logger.warning(f"MCP: Location not found or inactive: {location_id_str}")
                return []

            stmt = select(
                Activity.id,
                Activity.name,
                Activity.category,
                Activity.price_min,
                Activity.price_max,
                Activity.duration,
                Activity.location_id,
                Activity.is_active
            ).where(Activity.location_id == location_id, Activity.is_active == True)
            
            if category:
                stmt = stmt.where(Activity.category == category)

            result = await session.execute(stmt)
            activities = result.all()
            return [
                {
                    "id": str(act.id),
                    "name": act.name,
                    "category": act.category,
                    "price_min": act.price_min,
                    "price_max": act.price_max,
                    "duration": act.duration,
                    "location_id": str(act.location_id)
                }
                for act in activities
            ]
        except Exception as e:
            logger.error(f"MCP: Error fetching activities for location {location_id_str}: {e}", exc_info=True)
            raise ValueError(f"Failed to fetch activities: {e}")

@mcp.tool()
async def get_hotels_by_location(location_id_str: str) -> List[Dict[str, Any]]:
    """
    Retrieves hotels available at a specific location (typically a 'HotelArea'), using the Location ID obtained from `get_locations_by_destination`.

    Args:
        location_id_str: The unique identifier (UUID string) of the location.

    Returns:
        A list of dictionaries, each representing a hotel with its full details: 'id', 'name', 'amenities' (as a JSON object), and 'location_id'. Use the 'id' from this list when adding hotel stays to a custom itinerary.
        Example: [{"id": "3820e8cd-5344-4987-8bc3-5959a47b5738", "name": "Budget Hotel Patong", "amenities": {"pool": false, "wifi": true, "rating": 3, "price_category": "Budget"}, "location_id": "..."}]
    """
    logger.info(f"MCP: Fetching hotels for location_id: {location_id_str}")
    try:
        location_id = uuid.UUID(location_id_str)
    except ValueError:
        logger.error(f"MCP: Invalid location_id format: {location_id_str}")
        raise ValueError("Invalid location_id format. It must be a valid UUID.")

    async for session in get_db_session():
        try:
            loc_check = await session.get(Location, location_id)
            if not loc_check or not loc_check.is_active:
                logger.warning(f"MCP: Location not found or inactive: {location_id_str}")
                return []

            result = await session.execute(
                select(Hotel)
                .where(Hotel.location_id == location_id, Hotel.is_active == True)
            )
            hotels = result.scalars().all()
            return [
                {
                    "id": str(hot.id),
                    "name": hot.name,
                    "amenities": hot.amenities,
                    "location_id": str(hot.location_id)
                }
                for hot in hotels
            ]
        except Exception as e:
            logger.error(f"MCP: Error fetching hotels for location {location_id_str}: {e}", exc_info=True)
            raise ValueError(f"Failed to fetch hotels: {e}")

@mcp.tool()
async def get_transport_modes() -> List[Dict[str, Any]]:
    """
    Retrieves all available transport modes (e.g., Ferry, Taxi). Use this to find the Mode ID needed for transfers in a custom itinerary.

    Returns:
        A list of dictionaries, each representing a transport mode with its 'id' (UUID string), 'code' (enum string like 'taxi', 'ferry'), and 'name'.
        Example: [{"id": "9ff6864e-16e0-4de6-9d9b-ca93c7e6af99", "code": "taxi", "name": "Taxi / Grab"}]
    """
    logger.info("MCP: Fetching all transport modes")
    async for session in get_db_session():
        try:
            result = await session.execute(select(TransportMode).where(TransportMode.is_active == True))
            modes = result.scalars().all()
            return [
                {"id": str(mode.id), "code": mode.code.value, "name": mode.name}
                for mode in modes
            ]
        except Exception as e:
            logger.error(f"MCP: Error fetching transport modes: {e}", exc_info=True)
            raise ValueError(f"Failed to fetch transport modes: {e}")

@mcp.tool()
async def create_custom_itinerary(itinerary_data_json: str) -> Dict[str, Any]:
    """
    Creates a new custom travel itinerary from scratch based on the provided JSON data. Also used for saving modifications based on a recommended itinerary.

    **IMPORTANT INTERACTION GUIDELINES FOR CLAUDE:**
    1. ALWAYS start by using get_recommended_itinerary to search for template-based options BEFORE offering to create a custom itinerary
    2. Only proceed with creating a fully custom itinerary if:
       - The user explicitly requests it AFTER seeing template options
       - OR no suitable templates are available 
    3. When suggesting custom options, PRESENT ACTUAL LISTS of available options by calling the appropriate tools:
       - For hotels: Use get_hotels_by_location() and show 3-5 options with their amenities
       - For activities: Use get_activities_by_location() and present categorized lists of activities
       - Example presentation: "Here are some popular activities in Patong Beach:
         * Adventure:
           - Island Hopping Tour (6 hours, 3000-4500 INR)
           - Scuba Diving (3 hours, 5000-7000 INR)
         * Culture:
           - Temple Tour (4 hours, 1500-2500 INR)"
    4. ALLOW THE USER TO CHOOSE from these actual options rather than guessing or making up activities
    5. If creating a multi-day itinerary, ask about EACH DAY separately to avoid overwhelming the user

    **Workflow:**
    1. **Understand Goal:** Determine if the user wants a fully custom plan or modifications to a recommendation.
    2. **Gather IDs:**
        - For a fully custom plan: Use `get_destinations`, `get_locations_by_destination`, `get_hotels_by_location`, `get_activities_by_location`, `get_transport_modes` sequentially to gather all necessary Destination, Location, Hotel, Activity, and Transport Mode IDs based on user preferences.
        - If modifying a recommendation: You might already have some details from the `get_recommended_itinerary` output. Use the fetching tools to find IDs for any *new* items the user wants to add or change.
    3. **Construct JSON:** Carefully build the JSON payload string using the exact UUIDs obtained. The structure must precisely match the example below. **Consider activity durations** (available via `get_activities_by_location`) and typical travel times to ensure the schedule for each day is realistic (e.g., allow ~6-8 hours for sleep, don't exceed ~16-18 hours of scheduled activities/transfers per day).
    4. **Execute:** Call this tool (`create_custom_itinerary`) with the complete, valid JSON string.

    **Important:** Always use the fetching tools to get correct, current UUIDs. Do not guess IDs.

    Args:
        itinerary_data_json: A JSON string representing the complete itinerary details.

 JSON DATA STRUCTURE GUIDE:
    - traveler_name: String - Name of the traveler
    - start_date: String - Date in YYYY-MM-DD format
    - nights: Integer - Number of nights (minimum 1)
    - meta: Object - Additional metadata
      - purpose: String - Purpose of travel (e.g., "Vacation", "Business")
      - budget: Number - Budget amount
    - days: Array - List of itinerary day objects
      - day_number: Integer - Sequential day number
      - date: String - Date in YYYY-MM-DD format
      - notes: String - Optional notes for this day
      - hotel_stay: Object or null - Hotel details if staying overnight
        - hotel_id: String - UUID of hotel
        - check_in_time: String - Check-in time in HH:MM:SS format
      - activities: Array - List of activities for this day
        - activity_id: String - UUID of activity
        - timeslot: String - Time slot (Morning, Afternoon, or Evening)
      - transfers: Array - List of transfers on this day
        - mode_id: String - UUID of transport mode
        - from_location_id: String - UUID of departure location
        - to_location_id: String - UUID of destination location
        - departure_time: String - Departure time in HH:MM:SS format
    
    IMPORTANT: When generating the JSON, do NOT include any comments or annotations within the JSON structure.
    All property names must be valid JSON keys without explanation comments.
    
    Expected JSON payload format:
    this is expected format only any of the value cant be taken if from here automatically:
    dates are just exapmles nothing more
    ```json
    {
      "traveler_name": "NAME",
      "start_date": "2024-09-15",
      "nights": 1,
      "meta": {
        "purpose": "Vacation",
        "budget": 5000
      },
      "days": [
        {
          "day_number": 1,
          "date": "2024-09-15",
          "notes": "Arrival and check-in",
          "hotel_stay": {
            "hotel_id": "UUID-HOTEL",
            "check_in_time": "14:00:00"
          },
          "activities": [
            {
              "activity_id": "UUID-ACTIVITY",
              "timeslot": "Evening"
            }
          ],
          "transfers": []
        },
        {
          "day_number": 2,
          "date": "2024-09-16",
          "notes": "Departure",
          "hotel_stay": null,
          "activities": [],
          "transfers": [
            {
              "mode_id": "UUID-TRANSPORT",
              "from_location_id": "UUID-LOCATION_FROM",
              "to_location_id": "UUID-LOCATION_TO",
              "departure_time": "10:00:00"
            }
          ]
        }
      ]
    }
    ```

    Returns:
        A dictionary representing the created itinerary if successful, including its new ID.
        Returns a dictionary with an 'error' key if creation fails due to invalid JSON, missing/invalid IDs, or other issues.
    """
    logger.info("MCP: Received request to create custom itinerary.")
    try:
        # Parse the JSON to validate it
        itinerary_data = json.loads(itinerary_data_json)
        # Note: We're not using ItineraryCreate.model_validate here anymore
        # since we're forwarding the JSON directly to the API
    except json.JSONDecodeError as e:
        logger.error(f"MCP: Invalid JSON provided: {e}")
        return {"error": f"Invalid JSON format: {e}"}
    
    # Use httpx to make a POST request to the API endpoint
    try:
        # Use localhost:8000 or appropriate server URL
        api_url = "http://localhost:8000/api/v1/itineraries"
        
        # Make the POST request with the JSON data
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                json=itinerary_data,  # Send the parsed JSON as the request body
                timeout=30.0  # Set an appropriate timeout
            )
            
            # Check if the request was successful
            if response.status_code == 201:  # 201 Created
                logger.info("MCP: Successfully created itinerary via API")
                return response.json()
            else:
                logger.error(f"MCP: API returned error {response.status_code}: {response.text}")
                return {
                    "error": f"API error ({response.status_code}): {response.text}",
                    "details": response.json() if response.headers.get("content-type") == "application/json" else None
                }
    except httpx.RequestError as e:
        logger.error(f"MCP: HTTP request error: {e}")
        return {"error": f"Failed to connect to API: {e}"}
    except Exception as e:
        logger.error(f"MCP: Unexpected error creating itinerary: {e}", exc_info=True)
        return {"error": f"Unexpected error: {e}"}

@mcp.tool()
async def get_recommended_itinerary(
    nights: int,
    start_date_str: str,
    destination_id_str: str,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None
) -> dict[str, Any]:
    """
    Generates an itinerary based on a pre-defined template. Use this for simpler requests or as a starting point for customization.

    **IMPORTANT INTERACTION GUIDELINES FOR CLAUDE:**
    1. ALWAYS ask the user first: "Would you like me to suggest a complete itinerary based on templates, or would you prefer to build one step-by-step with your input?"
    2. If using a template, EXPLAIN that you'll be using a template that matches their criteria and they can modify it later
    3. AFTER showing the recommended itinerary, EXPLICITLY ASK: "How does this itinerary look? Would you like to make any changes to the activities, hotels, or schedule?"
    4. If the user wants changes, use get_activities_by_location() to SHOW ACTUAL ALTERNATIVES from the database that they can choose from

    This tool finds the best matching template based on the criteria. Templates contain pre-selected activities and hotels.
    The template itself contains destination information in its 'destinations' field (a list of {"id": "uuid", "name": "Dest Name"}).
    The generated itinerary includes all details (hotels, activities, transfers with their IDs and names).

    If the user likes the recommendation but wants changes, use the details from the response of this tool as a base, fetch any additional IDs needed using the catalogue tools, and then call `create_custom_itinerary` with the modified structure.

    Args:
        nights: The number of nights for the trip.
        start_date_str: The start date in 'YYYY-MM-DD' format.
        destination_id_str: The UUID for the desired primary destination (obtained from `get_destinations`). The tool finds templates including this destination.
        budget_min: Optional minimum budget in INR.
        budget_max: Optional maximum budget in INR.

    Returns:
        A dictionary representing the fully generated itinerary (including 'id', 'traveler_name', 'start_date', 'nights', 'meta', and detailed 'days' list with resolved hotel/activity/transfer names and IDs) if successful.
        Returns a dictionary with an 'error' or 'message' key if no template is found or an error occurs.
    """
    logger.info(f"MCP: Received recommendation request: nights={nights}, start_date={start_date_str}, destination={destination_id_str}, budget=({budget_min}-{budget_max})")
    try:
        start_date = date.fromisoformat(start_date_str)
        if start_date < date.today():
            logger.error("MCP: Start date cannot be in the past.")
            raise ValueError("Start date cannot be in the past.")
    except ValueError as e:
        logger.error(f"MCP: Invalid start_date format: {start_date_str}. Error: {e}")
        raise ValueError(f"Invalid start_date: {e}. Use 'YYYY-MM-DD' format and ensure it's not in the past.")

    try:
        destination_id = uuid.UUID(destination_id_str)
    except ValueError:
        logger.error(f"MCP: Invalid destination_id format: {destination_id_str}")
        raise ValueError("Invalid destination_id format. It must be a valid UUID.")

    async for session in get_db_session():
        try:
            logger.info("MCP: Picking template...")
            template = await pick_template(
                db=session,
                nights=nights,
                destination_id=destination_id,
                budget_min=budget_min,
                budget_max=budget_max
            )

            if not template:
                logger.warning("MCP: No suitable template found.")
                return {"message": "No suitable template found for the given criteria."}

            logger.info(f"MCP: Found template {template.id}. Materialising...")
            try:
                generated_itinerary: ItineraryRead = await materialise_template(
                    db=session,
                    template_id=template.id,
                    start_date=start_date,
                    traveler_name=f"Recommended Itinerary ({template.name})"
                )
                logger.info(f"MCP: Successfully materialised itinerary {generated_itinerary.id}")
                return generated_itinerary.model_dump(mode='json')
            except ValueError as ve:
                logger.error(f"MCP: Error during materialisation: {ve}")
                return {"error": f"Could not materialise template: {ve}"}
            except Exception as e:
                logger.exception("MCP: Unexpected error during materialisation.")
                raise ValueError(f"Error materialising itinerary: {e}")

        except Exception as e:
            logger.exception("MCP: Error processing recommendation request.")
            raise ValueError(f"Error getting recommendation: {e}")

if __name__ == "__main__":
    mcp.run(transport='stdio')
