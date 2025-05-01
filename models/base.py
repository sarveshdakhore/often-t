from core.database import Base
from core.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True
    # Common fields and methods can go here if needed
