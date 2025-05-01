from typing import Optional
from pydantic import BaseModel

class ActivityBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    duration: Optional[int] = None
    description: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    pass

class ActivityInDBBase(ActivityBase):
    id: int

    class Config:
        orm_mode = True

class Activity(ActivityInDBBase):
    pass

class ActivityInDB(ActivityInDBBase):
    pass