from pydantic import BaseModel, Field
from typing import Annotated # Import Annotated

class PaginationParams(BaseModel):
    # Use Annotated for constraints
    limit: Annotated[int, Field(ge=1, le=100)] = Field(10, description="Number of items to return per page.")
    offset: Annotated[int, Field(ge=0)] = Field(0, description="Number of items to skip.")
