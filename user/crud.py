import os
from typing import Type, Optional, Dict, Any

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, File, UploadFile
from sqlalchemy.orm import selectinload
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape

from shared.core.models import User, Preferences
from user.schemas import UserModel, GeoPoint, UserShowMe

from shared.clients.redis.RedisClient import redis_client

from auth.jwt_auth import auth_user_jwt



async def get_users(session: AsyncSession):
    result = await session.execute(select(User).options(selectinload(User.preferences)).order_by(User.id))
    users = result.scalars().all()
    
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "preferences": {
                "sex": user.preferences.sex,
                "location": postgis_to_geopoint(user.preferences.location),
                "age_min": user.preferences.age_min,
                "age_max": user.preferences.age_max
            }
        }
        user_list.append(user_dict)
    
    return user_list


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()


async def get_user_by_id(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).options(selectinload(User.preferences)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_model = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "preferences": {
            "sex": user.preferences.sex,
            "location": postgis_to_geopoint(user.preferences.location),
            "age_min": user.preferences.age_min,
            "age_max": user.preferences.age_max
        }
    }
    
    return user_model


async def get_user_by_username(username: str, session: AsyncSession) -> User:
    stmt = select(User).options(selectinload(User.preferences)).where(User.username == username)
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

    location_wkt = user.preferences.location.to_wkt()
    location_postgis = WKTElement(location_wkt, srid=4326)

    user_db = User(
        username=user.username,
        password=hashed_password,
        email=user.email,
        preferences=Preferences(
            sex=user.preferences.sex,
            location=location_postgis,
            age_min=user.preferences.age_min,
            age_max=user.preferences.age_max
        )
    )

    session.add(user_db)
    await session.commit()
    await session.refresh(user_db, ['preferences'])
    
    return {
        "id": user_db.id,
        "username": user_db.username,
        "email": user_db.email,
        "preferences": {
            "sex": user_db.preferences.sex,
            "location": postgis_to_geopoint(user_db.preferences.location),
            "age_min": user_db.preferences.age_min,
            "age_max": user_db.preferences.age_max
        }
    }


def postgis_to_geopoint(postgis_point) -> Optional[GeoPoint]:
    if postgis_point is None:
        return None
    
    point = to_shape(postgis_point)
    
    return GeoPoint(latitude=point.y, longitude=point.x)


async def get_me(user_id: int, session: AsyncSession):
    result = await session.execute(select(User).options(selectinload(User.preferences)).where(User.id == user_id))
    user = result.scalars().first()
    user_model = UserShowMe(
        username=user.username,
        email=user.email,
        photo=user.photo if user.photo else None,
        preferences={
            "sex": user.preferences.sex,
            "location": postgis_to_geopoint(user.preferences.location),
            "age_min": user.preferences.age_min,
            "age_max": user.preferences.age_max
        },
    )
    return user_model


async def upload_photo(user_id, session: AsyncSession, file):
    result = await session.execute(select(User).where(User.id==user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_extension = file.filename.split(".")[-1]
    file_path = f"static/users/{user_id}.{file_extension}"
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    file_url = f"/static/users/{user_id}.{file_extension}"
    await session.flush()
    user.photo = file_url
    session.add(user)
    await session.commit()

    return {"photo_url": file_url}