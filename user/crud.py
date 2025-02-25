from typing import Type

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from core.models import User, Preferences
from user.schemas import UserCreate, UserModel


async def get_users(session: AsyncSession):
    stmt = await session.execute(select(User).options(selectinload(User.preferences)).order_by(User.id))
    return stmt.scalars().all()


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Type[User]:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def get_user_by_username(username: str, session: AsyncSession) -> User:
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)

    user = result.scalar_one_or_none()
    if user is not None:
        return user
    else:
        raise ValueError('User with this id not found')


async def registrate_user(user: UserModel, session: AsyncSession):
    result = await session.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail='User with this username already exists')

    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())

    user_db = User(
        username=user.username,
        password=hashed_password,
        email=user.email,
        preferences=Preferences(
            sex=user.preferences.sex,
            latitude=user.preferences.latitude,
            longtitude=user.preferences.longtitude,
            age_min=user.preferences.age_min,
            age_max=user.preferences.age_max
        )
    )

    session.add(user_db)
    await session.commit()
    await session.refresh(user_db, ['preferences'])

    return user_db


async def get_me(user_id: int, session: AsyncSession):
    result = await session.execute(select(User).options(selectinload(User.preferences)).where(User.id == user_id))
    user = result.scalars().first()

    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

