from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.ext.declarative import declared_attr
from geoalchemy2 import Geography  # PostGIS

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Genre(Enum):
    male = 'male'
    female = 'female'


class Preferences(Base):
    sex: Mapped[Genre] = mapped_column(nullable=False)

    location: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    age_min: Mapped[int] = mapped_column(nullable=False)
    age_max: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped['User'] = relationship('User', back_populates='preferences')