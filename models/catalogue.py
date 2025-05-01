import enum
from sqlalchemy import Column, String, ForeignKey, Enum, Float, Index, JSON, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB  # Remove POINT as it's not available
from sqlalchemy.orm import relationship
from .base import BaseModel

# Uncomment if using PostGIS
# from geoalchemy2 import Geometry

class Destination(BaseModel):
    __tablename__ = "destinations"
    name = Column(String, nullable=False, unique=True)
    # Use POINT for PostGIS, or separate lat/lon floats
    # coordinates = Column(Geometry(geometry_type='POINT', srid=4326), index=True) # PostGIS example
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    locations = relationship("Location", back_populates="destination")

class Location(BaseModel):
    __tablename__ = "locations"
    destination_id = Column(ForeignKey("destinations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String) # e.g., 'Airport', 'HotelArea', 'AttractionSite'

    destination = relationship("Destination", back_populates="locations")
    hotels = relationship("Hotel", back_populates="location")
    activities = relationship("Activity", back_populates="location")
    transfers_from = relationship("DayTransfer", foreign_keys="[DayTransfer.from_location_id]", back_populates="from_location")
    transfers_to = relationship("DayTransfer", foreign_keys="[DayTransfer.to_location_id]", back_populates="to_location")

class Hotel(BaseModel):
    __tablename__ = "hotels"
    location_id = Column(ForeignKey("locations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    amenities = Column(JSONB) # Store amenities as JSON

    location = relationship("Location", back_populates="hotels")
    day_hotels = relationship("DayHotel", back_populates="hotel")
    template_days = relationship("TemplateDay", foreign_keys="[TemplateDay.hotel_id]", back_populates="hotel")


class Activity(BaseModel):
    __tablename__ = "activities"
    location_id = Column(ForeignKey("locations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, index=True) # e.g., 'Adventure', 'Culture', 'Relaxation'
    description = Column(String)
    price_min = Column(Float) # Optional min price in INR
    price_max = Column(Float) # Optional max price in INR
    duration = Column(String) # Added: e.g., "2 hours", "Half Day", "Full Day", "Approx. 30 mins"

    location = relationship("Location", back_populates="activities")
    day_activities = relationship("DayActivity", back_populates="activity")
    template_days = relationship("TemplateDay", foreign_keys="[TemplateDay.activity_id]", back_populates="activity")


class TransportModeEnum(enum.Enum):
    FLIGHT = "flight"
    FERRY = "ferry"
    BUS = "bus"
    TAXI = "taxi"
    PRIVATE_CAR = "private_car"
    MINIVAN = "minivan"

class TransportMode(BaseModel):
    __tablename__ = "transport_modes"
    code = Column(Enum(TransportModeEnum), nullable=False, unique=True)
    name = Column(String, nullable=False) # e.g., "Speedboat Ferry"

    day_transfers = relationship("DayTransfer", back_populates="mode")
    template_days = relationship("TemplateDay", foreign_keys="[TemplateDay.transfer_id]", back_populates="transfer_mode") # Assuming transfer_id links here for simplicity in template

# Add GIST index if using PostGIS
# Index('ix_locations_coordinates', Location.coordinates, postgresql_using='gist')
