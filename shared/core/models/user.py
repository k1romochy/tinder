from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Enum as SQLEnum

from .base import Base

if TYPE_CHECKING:
    from .cookie import SessionModel
    from .preferences import Preferences
    from .like import Like, Match


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
    
    # Связи с лайками и матчами
    likes_given: Mapped[List['Like']] = relationship('Like', foreign_keys='Like.from_user_id', 
                                                     back_populates='from_user', cascade="all, delete-orphan")
    likes_received: Mapped[List['Like']] = relationship('Like', foreign_keys='Like.to_user_id', 
                                                       back_populates='to_user', cascade="all, delete-orphan")
    matches_as_user1: Mapped[List['Match']] = relationship('Match', foreign_keys='Match.user1_id', 
                                                          back_populates='user1', cascade="all, delete-orphan")
    matches_as_user2: Mapped[List['Match']] = relationship('Match', foreign_keys='Match.user2_id', 
                                                          back_populates='user2', cascade="all, delete-orphan")
