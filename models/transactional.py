from sqlalchemy import Column, String, ForeignKey, Integer, Date, Time, UniqueConstraint, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Itinerary(BaseModel):
    __tablename__ = "itineraries"
    organisation_id = Column(UUID(as_uuid=True), nullable=True, index=True) # Optional multi-tenancy
    traveler_name = Column(String)
    start_date = Column(Date, nullable=False)
    nights = Column(Integer, nullable=False)
    meta = Column(JSONB) # Store extra info like booking refs, total cost etc.

    days = relationship("ItineraryDay", back_populates="itinerary", cascade="all, delete-orphan")

class ItineraryDay(BaseModel):
    __tablename__ = "itinerary_days"
    itinerary_id = Column(ForeignKey("itineraries.id"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False) # 1-based day number
    date = Column(Date, nullable=False)
    notes = Column(String)

    itinerary = relationship("Itinerary", back_populates="days")
    hotel_stay = relationship("DayHotel", back_populates="itinerary_day", uselist=False, cascade="all, delete-orphan") # One-to-one
    activities = relationship("DayActivity", back_populates="itinerary_day", cascade="all, delete-orphan")
    transfers = relationship("DayTransfer", back_populates="itinerary_day", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('itinerary_id', 'day_number', name='uq_itinerary_day_number'),
        Index('ix_itinerary_day_itinerary_date', 'itinerary_id', 'date'),
    )

class DayHotel(BaseModel):
    __tablename__ = "day_hotels"
    itinerary_day_id = Column(ForeignKey("itinerary_days.id"), nullable=False, unique=True, index=True) # Enforce one-to-one
    hotel_id = Column(ForeignKey("hotels.id"), nullable=False, index=True)
    check_in_time = Column(Time)
    template = Column(Boolean, default=False, nullable=False) # Added template flag

    itinerary_day = relationship("ItineraryDay", back_populates="hotel_stay")
    hotel = relationship("Hotel", back_populates="day_hotels")

class DayActivity(BaseModel):
    __tablename__ = "day_activities"
    itinerary_day_id = Column(ForeignKey("itinerary_days.id"), nullable=False, index=True)
    activity_id = Column(ForeignKey("activities.id"), nullable=False, index=True)
    timeslot = Column(String) # e.g., "09:00-12:00" or "Afternoon"
    template = Column(Boolean, default=False, nullable=False) # Re-added template flag

    itinerary_day = relationship("ItineraryDay", back_populates="activities")
    activity = relationship("Activity", back_populates="day_activities")

class DayTransfer(BaseModel):
    __tablename__ = "day_transfers"
    itinerary_day_id = Column(ForeignKey("itinerary_days.id"), nullable=False, index=True)
    mode_id = Column(ForeignKey("transport_modes.id"), nullable=False, index=True)
    from_location_id = Column(ForeignKey("locations.id"), nullable=False, index=True)
    to_location_id = Column(ForeignKey("locations.id"), nullable=False, index=True)
    departure_time = Column(Time)
    template = Column(Boolean, default=False, nullable=False)  # Re-added template flag
    # Optional: arrival_time, duration, booking_ref

    itinerary_day = relationship("ItineraryDay", back_populates="transfers")
    mode = relationship("TransportMode", back_populates="day_transfers")
    from_location = relationship("Location", foreign_keys=[from_location_id], back_populates="transfers_from")
    to_location = relationship("Location", foreign_keys=[to_location_id], back_populates="transfers_to")
