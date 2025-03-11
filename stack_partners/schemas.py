from pydantic import BaseModel, ConfigDict
from typing import List

class UserRecomendationResponse(BaseModel):
    id: int
    name: str
    description: str
    age: int
    photos: List[str]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
