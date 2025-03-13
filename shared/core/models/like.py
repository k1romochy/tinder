from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Like(Base):
    """Модель для лайков между пользователями"""
    
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)  # Для "отмены" лайка без удаления записи
    
    # Связи
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="likes_given")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="likes_received")
    
    # Уникальное ограничение для предотвращения дублирования лайков
    __table_args__ = (
        UniqueConstraint('from_user_id', 'to_user_id', name='uq_user_like'),
    )


class Match(Base):
    """Модель для матчей (взаимных лайков) между пользователями"""
    
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)  # Для деактивации матча без удаления
    
    # Связи
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")
    
    # Уникальное ограничение для предотвращения дублирования матчей
    # Пары пользователей всегда хранятся с меньшим ID первым для консистентности
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='uq_user_match'),
    ) 