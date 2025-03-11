from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Enum as SQLEnum

from .base import Base

if TYPE_CHECKING:
    from .cookie import SessionModel
    from .preferences import Preferences


class Active(Enum):
    active = 'active'
    inactive = 'inactive'


class User(Base):
    username: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[bytes] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[str] = mapped_column(nullable=False, server_default='User')
    photo: Mapped[str | None] = mapped_column(server_default=None)
    active: Mapped[Active] = mapped_column(SQLEnum(Active), nullable=False, default=Active.active)
    description: Mapped[str | None] = mapped_column(nullable=True)

    session: Mapped['SessionModel'] = relationship('SessionModel', back_populates='user',
                                                    cascade="all, delete-orphan")
    preferences: Mapped['Preferences'] = relationship('Preferences', back_populates='user')
