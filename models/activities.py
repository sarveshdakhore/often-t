from sqlalchemy import Column, String, UUID, Boolean, Float, Integer, DateTime
from sqlalchemy.sql import func
import uuid
from .base import Base

class Activities(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)  # Add the missing description column
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())