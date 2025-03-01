from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from .cookie import SessionModel
    from .preferences import Preferences


class User(Base):
    username: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[bytes] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[str] = mapped_column(nullable=False, server_default='User')
    photo: Mapped[str | None] = mapped_column(server_default=None)

    session: Mapped['SessionModel'] = relationship('SessionModel', back_populates='user',
                                                    cascade="all, delete-orphan")
    preferences: Mapped['Preferences'] = relationship('Preferences', back_populates='user')