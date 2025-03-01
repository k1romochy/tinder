from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from .user import User


class Genre(Enum):
    male = 'male'
    female = 'female'


class Preferences(Base):
    sex: Mapped[Genre] = mapped_column(SQLEnum(Genre), nullable=False)

    latitude: Mapped[float] = mapped_column(nullable=False)
    longtitude: Mapped[float] = mapped_column(nullable=False)

    age_min: Mapped[int] = mapped_column(nullable=False)
    age_max: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column((ForeignKey('user.id')))
    user: Mapped['User'] = relationship('User', back_populates='preferences')

