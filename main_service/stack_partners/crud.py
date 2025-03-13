import os
from typing import Type

import bcrypt
from dotenv import load_dotenv
from geoalchemy2.functions import ST_DWithin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, File
from sqlalchemy.orm import selectinload, joinedload

from shared.core.models import User, Preferences
from user.schemas import UserCreate, UserModel

from shared.clients.s3.S3Client import s3_client


async def get_users_with_preferences(user_id: int):
    pass


async def get_nearby_users(session: AsyncSession, user_id: int, radius: int):
    result = await session.execute(select(Preferences.location).where(Preferences.user_id == user_id))
    user_location = result.scalar()

    if not user_location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    query = (
        select(Preferences)
        .where(
            Preferences.user_id != user_id,
            ST_DWithin(Preferences.location, user_location, radius)
        )
    )

    result = await session.execute(query)
    users = result.scalars().all()

    return [user.user_id for user in users]

async def get_users_with_ages_preferences(user_id: int, session: AsyncSession):
    result = await session.execute(select(User).where(User.id == user_id).options(joinedload(User.preferences)))
    user = result.scalar_one_or_none()

    proposed_users = await session.execute()