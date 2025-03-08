from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, Any

from core.models.preferences import Genre


class GeoPoint(BaseModel):
    """Модель для представления географической точки."""
    latitude: float
    longitude: float
    
    def to_wkt(self) -> str:
        """Преобразует точку в формат WKT для PostGIS."""
        return f"POINT({self.longitude} {self.latitude})"
    
    @classmethod
    def from_wkt(cls, wkt: Optional[str]) -> Optional['GeoPoint']:
        """Создает GeoPoint из строки WKT."""
        if not wkt or not isinstance(wkt, str) or not wkt.startswith("POINT"):
            return None
        
        try:
            # Формат: POINT(longitude latitude)
            coordinates = wkt.replace("POINT(", "").replace(")", "").split()
            if len(coordinates) != 2:
                return None
            
            return cls(longitude=float(coordinates[0]), latitude=float(coordinates[1]))
        except Exception:
            return None


class Preferences(BaseModel):
    sex: Genre
    location: GeoPoint
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
