import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr

class UUIDMixin:
    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class SoftDeleteMixin:
    @declared_attr
    def is_active(cls):
        return Column(Boolean, default=True, nullable=False, index=True)

    def soft_delete(self):
        self.is_active = False

    def activate(self):
        self.is_active = True
