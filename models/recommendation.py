from sqlalchemy import Column, String, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from .base import BaseModel
from sqlalchemy.dialects.postgresql import UUID, JSONB # Import JSONB

class Template(BaseModel):
    __tablename__ = "templates"
    name = Column(String, nullable=False, unique=True)
    nights = Column(Integer, nullable=False, index=True)
    style = Column(String, index=True) # e.g., 'Relax', 'Adventure', 'Family', 'Luxury'
    budget = Column(String, index=True) # e.g., 'Budget', 'Mid-range', 'Luxury'
    popularity = Column(Float, default=0.0) # Simple popularity score
    avg_cost = Column(Float) # Estimated average cost in INR
    destinations = Column(JSONB) # Added destinations JSONB field. Stores list like [{"id": "uuid", "name": "Dest Name"}]

    template_days = relationship("TemplateDay", back_populates="template", cascade="all, delete-orphan")

class TemplateDay(BaseModel):
    __tablename__ = "template_days"
    template_id = Column(ForeignKey("templates.id"), nullable=False, index=True)
    day_offset = Column(Integer, nullable=False) # 0-based day offset from start
    hotel_id = Column(ForeignKey("hotels.id"), nullable=True, index=True) # Optional: Suggest a hotel
    activity_id = Column(ForeignKey("activities.id"), nullable=True, index=True) # Optional: Suggest an activity
    transfer_id = Column(ForeignKey("transport_modes.id"), nullable=True, index=True) # Optional: Suggest a transfer type (simplified)
    # Note: A more complex template might need TemplateDayActivity, TemplateDayTransfer etc.

    template = relationship("Template", back_populates="template_days")
    hotel = relationship("Hotel", foreign_keys=[hotel_id], back_populates="template_days")
    activity = relationship("Activity", foreign_keys=[activity_id], back_populates="template_days")
    transfer_mode = relationship("TransportMode", foreign_keys=[transfer_id], back_populates="template_days")

    # __table_args__ = (UniqueConstraint('template_id', 'day_offset', name='uq_template_day_offset'),) # Might need multiple entries per day
