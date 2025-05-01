from pydantic import BaseModel as PydanticBaseModel, ConfigDict

class BaseSchema(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True) # Enable ORM mode
