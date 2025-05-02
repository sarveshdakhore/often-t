import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.catalogue import (
    Destination, Location, Hotel, Activity, TransportMode, TransportModeEnum
)
from models.transactional import (
     DayActivity, DayTransfer, DayHotel
)
from models.recommendation import Template, TemplateDay

def seed_data(db: Session):
    # Check if data already exists to avoid duplicates
    if db.query(Destination).count() > 0:
        print("Data already seeded. Skipping basic seed operation.")
        # We can still add more templates if needed
        seed_additional_templates(db)
        return

    # Seed basic data (destinations, locations, hotels, etc.)
    seed_basic_data(db)
    
    # Seed templates
    seed_templates(db)

def seed_basic_data(db: Session):
    print("Seeding basic data...")
    
    # Create destinations
    bali = Destination(name="Bali", latitude=-8.4095178, longitude=115.188916)
    phuket = Destination(name="Phuket", latitude=7.9519, longitude=98.3381)
    
    db.add_all([bali, phuket])
    db.commit()
    
    # Create locations for Bali
    denpasar = Location(destination_id=bali.id, name="Denpasar", kind="Airport")
    ubud = Location(destination_id=bali.id, name="Ubud", kind="HotelArea")
    seminyak = Location(destination_id=bali.id, name="Seminyak", kind="HotelArea")
    kuta = Location(destination_id=bali.id, name="Kuta", kind="HotelArea")
    
    # Create locations for Phuket
    phuket_airport = Location(destination_id=phuket.id, name="Phuket International Airport", kind="Airport")
    patong = Location(destination_id=phuket.id, name="Patong", kind="HotelArea")
    kata = Location(destination_id=phuket.id, name="Kata", kind="HotelArea")
    
    db.add_all([denpasar, ubud, seminyak, kuta, phuket_airport, patong, kata])
    db.commit()
    
    # Create hotels
    # Bali hotels
    four_seasons = Hotel(location_id=ubud.id, name="Four Seasons Resort Bali at Sayan", amenities={"wifi": True, "pool": True, "spa": True})
    w_bali = Hotel(location_id=seminyak.id, name="W Bali - Seminyak", amenities={"wifi": True, "pool": True, "beach_access": True})
    hard_rock = Hotel(location_id=kuta.id, name="Hard Rock Hotel Bali", amenities={"wifi": True, "pool": True, "kids_club": True})
    
    # Phuket hotels
    amanpuri = Hotel(location_id=patong.id, name="Amanpuri", amenities={"wifi": True, "pool": True, "spa": True})
    shore = Hotel(location_id=kata.id, name="The Shore at Katathani", amenities={"wifi": True, "pool": True, "beach_access": True})
    
    db.add_all([four_seasons, w_bali, hard_rock, amanpuri, shore])
    db.commit()
    
    # Create activities
    # Bali activities
    ubud_activities = [
        Activity(location_id=ubud.id, name="Sacred Monkey Forest Sanctuary", category="Nature", price_min=3750, price_max=6000, duration=3.0),
        Activity(location_id=ubud.id, name="Tegallalang Rice Terraces", category="Sightseeing", price_min=1500, price_max=3000, duration=2.0),
        Activity(location_id=ubud.id, name="Ubud Art Market", category="Shopping", price_min=0, price_max=7500, duration=2.5),
        Activity(location_id=ubud.id, name="White Water Rafting", category="Adventure", price_min=5250, price_max=9000, duration=5.0),
    ]
    
    seminyak_activities = [
        Activity(location_id=seminyak.id, name="Seminyak Beach", category="Beach", price_min=0, price_max=0, duration=4.0),
        Activity(location_id=seminyak.id, name="Potato Head Beach Club", category="Relaxation", price_min=3750, price_max=15000, duration=6.0),
        Activity(location_id=seminyak.id, name="Seminyak Shopping", category="Shopping", price_min=0, price_max=22500, duration=3.0),
    ]
    
    kuta_activities = [
        Activity(location_id=kuta.id, name="Kuta Beach", category="Beach", price_min=0, price_max=0, duration=4.0),
        Activity(location_id=kuta.id, name="Waterbom Bali", category="Adventure", price_min=3000, price_max=4500, duration=6.0),
        Activity(location_id=kuta.id, name="Surfing Lesson", category="Adventure", price_min=2250, price_max=7500, duration=2.0),
    ]
    
    # Phuket activities
    patong_activities = [
        Activity(location_id=patong.id, name="Patong Beach", category="Beach", price_min=0, price_max=0, duration=4.0),
        Activity(location_id=patong.id, name="Bangla Road Nightlife", category="Nightlife", price_min=3750, price_max=15000, duration=5.0),
        Activity(location_id=patong.id, name="Jet Skiing", category="Adventure", price_min=3000, price_max=6000, duration=1.5),
    ]
    
    kata_activities = [
        Activity(location_id=kata.id, name="Kata Beach", category="Beach", price_min=0, price_max=0, duration=4.0),
        Activity(location_id=kata.id, name="Kata Viewpoint", category="Sightseeing", price_min=0, price_max=0, duration=1.0),
        Activity(location_id=kata.id, name="Thai Cooking Class", category="Culture", price_min=4500, price_max=7500, duration=3.0),
    ]
    
    all_activities = ubud_activities + seminyak_activities + kuta_activities + patong_activities + kata_activities
    db.add_all(all_activities)
    db.commit()
    
    # Create transport modes
    transport_modes = [
        TransportMode(code=TransportModeEnum.FLIGHT, name="Flight"),
        TransportMode(code=TransportModeEnum.FERRY, name="Ferry"),
        TransportMode(code=TransportModeEnum.BUS, name="Bus"),
        TransportMode(code=TransportModeEnum.TAXI, name="Taxi"),
        TransportMode(code=TransportModeEnum.PRIVATE_CAR, name="Private Car"),
        TransportMode(code=TransportModeEnum.MINIVAN, name="Minivan"),
    ]
    
    db.add_all(transport_modes)
    db.commit()
    
    print("Basic data seeded successfully")

def seed_templates(db: Session):
    print("Seeding initial templates...")
    
    # Get all the entities we need for creating templates
    hotels = db.query(Hotel).all()
    activities_by_location = {}
    for location in db.query(Location).all():
        activities_by_location[location.id] = db.query(Activity).filter(Activity.location_id == location.id).all()
    
    transport_modes = db.query(TransportMode).all()
    taxi = next((m for m in transport_modes if m.code == TransportModeEnum.TAXI), None)
    
    # Create a few templates with varying lengths
    templates = [
        Template(name="Bali Adventure - 3 Days", description="Short adventure in Bali", days=3),
        Template(name="Relaxing Phuket - 5 Days", description="Relaxation in Phuket", days=5),
    ]
    
    db.add_all(templates)
    db.commit()
    
    # Create template days for the first template (Bali Adventure)
    bali_template = templates[0]
    
    # Day 1: Arrive in Ubud and stay at Four Seasons
    ubud_hotel = next((h for h in hotels if h.name == "Four Seasons Resort Bali at Sayan"), None)
    ubud_activities = activities_by_location.get(ubud_hotel.location_id, [])
    
    day1 = TemplateDay(template_id=bali_template.id, day_number=1, hotel_id=ubud_hotel.id)
    db.add(day1)
    db.commit()
    
    # Add day activities - mark as template activities
    if ubud_activities:
        activity1 = DayActivity(day_id=day1.id, activity_id=ubud_activities[0].id, template=True)
        activity2 = DayActivity(day_id=day1.id, activity_id=ubud_activities[1].id, template=True)
        db.add_all([activity1, activity2])
    
    # Day 2: Move to Seminyak
    seminyak_hotel = next((h for h in hotels if h.name == "W Bali - Seminyak"), None)
    seminyak_activities = activities_by_location.get(seminyak_hotel.location_id, [])
    
    day2 = TemplateDay(template_id=bali_template.id, day_number=2, hotel_id=seminyak_hotel.id)
    db.add(day2)
    db.commit()
    
    # Add transfer from Ubud to Seminyak - mark as template transfer
    transfer = DayTransfer(
        day_id=day2.id, 
        from_location_id=ubud_hotel.location_id, 
        to_location_id=seminyak_hotel.location_id, 
        mode_id=taxi.id,
        template=True
    )
    db.add(transfer)
    
    # Add day activities
    if seminyak_activities:
        activity3 = DayActivity(day_id=day2.id, activity_id=seminyak_activities[0].id, template=True)
        db.add(activity3)
    
    # Day 3: Stay in Seminyak
    day3 = TemplateDay(template_id=bali_template.id, day_number=3, hotel_id=seminyak_hotel.id)
    db.add(day3)
    db.commit()
    
    # Add day activities
    if seminyak_activities and len(seminyak_activities) > 1:
        activity4 = DayActivity(day_id=day3.id, activity_id=seminyak_activities[1].id, template=True)
        db.add(activity4)
    
    db.commit()
    print("Initial templates seeded successfully")

def seed_additional_templates(db: Session):
    """Add more templates ranging from 1 to 8 days"""
    print("Adding additional templates...")
    
    # Check how many templates we already have
    existing_count = db.query(Template).count()
    if existing_count >= 10:
        print("Already have 10+ templates. Skipping additional template creation.")
        return
    
    # Get all the entities we need for creating templates
    hotels = db.query(Hotel).all()
    locations = db.query(Location).all()
    activities_by_location = {}
    for location in locations:
        activities_by_location[location.id] = db.query(Activity).filter(Activity.location_id == location.id).all()
    
    transport_modes = db.query(TransportMode).all()
    taxi = next((m for m in transport_modes if m.code == TransportModeEnum.TAXI), None)
    
    # Create templates for different day ranges
    day_ranges = list(range(1, 9))
    styles = ["Adventure", "Relaxation", "Cultural", "Family", "Romantic", "Budget", "Luxury"]
    
    templates_to_create = 10 - existing_count
    
    for i in range(templates_to_create):
        days = random.choice(day_ranges)
        style = random.choice(styles)
        destination = "Bali" if random.random() > 0.5 else "Phuket"
        
        template = Template(
            name=f"{style} {destination} - {days} Days",
            description=f"{style} experience in {destination} for {days} days",
            days=days
        )
        db.add(template)
        db.commit()
        
        # Filter hotels by destination
        destination_obj = db.query(Destination).filter(Destination.name == destination).first()
        destination_locations = [loc for loc in locations if loc.destination_id == destination_obj.id]
        destination_hotels = [h for h in hotels if any(h.location_id == loc.id for loc in destination_locations)]
        
        # Create template days
        current_hotel = random.choice(destination_hotels)
        
        for day_num in range(1, days + 1):
            # Maybe change hotel every 2-3 days
            if day_num > 1 and random.random() < 0.3:
                new_hotel = random.choice([h for h in destination_hotels if h.id != current_hotel.id])
                if new_hotel:
                    current_hotel = new_hotel
            
            # Create template day
            template_day = TemplateDay(
                template_id=template.id, 
                day_number=day_num, 
                hotel_id=current_hotel.id
            )
            db.add(template_day)
            db.commit()
            
            # Add activities for this day
            day_activities = activities_by_location.get(current_hotel.location_id, [])
            if day_activities:
                # Select 1-3 random activities
                num_activities = min(random.randint(1, 3), len(day_activities))
                selected_activities = random.sample(day_activities, num_activities)
                
                for activity in selected_activities:
                    day_activity = DayActivity(
                        day_id=template_day.id, 
                        activity_id=activity.id,
                        template=True
                    )
                    db.add(day_activity)
            
            # Add transfer if hotel changed
            if day_num > 1 and template_day.hotel_id != db.query(TemplateDay).filter(
                TemplateDay.template_id == template.id, 
                TemplateDay.day_number == day_num - 1
            ).first().hotel_id:
                previous_day = db.query(TemplateDay).filter(
                    TemplateDay.template_id == template.id,
                    TemplateDay.day_number == day_num - 1
                ).first()
                
                previous_hotel = db.query(Hotel).filter(Hotel.id == previous_day.hotel_id).first()
                
                transfer = DayTransfer(
                    day_id=template_day.id,
                    from_location_id=previous_hotel.location_id,
                    to_location_id=current_hotel.location_id,
                    mode_id=taxi.id,
                    template=True
                )
                db.add(transfer)
        
        db.commit()
    
    print(f"Added {templates_to_create} additional templates")
