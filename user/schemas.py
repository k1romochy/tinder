from pydantic import BaseModel, ConfigDict, EmailStr

from core.models.preferences import Genre


class Preferences(BaseModel):
    sex: Genre
    latitude: float
    longtitude: float
    age_min: int
    age_max: int


class UserModel(BaseModel):
    username: str
    preferences: Preferences
    email: EmailStr


class User(UserModel):
    id: int

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class UserCreate(UserModel):
    password: str


class Photo(BaseModel):
    url: str
