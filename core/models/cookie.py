from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core.models.base import Base

if TYPE_CHECKING:
    from core.models.user import User


class SessionModel(Base):
    session_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    user: Mapped['User'] = relationship('User', back_populates='session')
