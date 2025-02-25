import os

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Form, HTTPException, status, Cookie
from fastapi.security import HTTPBearer
from sqlalchemy.orm import joinedload

from auth import utils as auth_utils
from core.config import settings
from core.models import SessionModel
from core.models.db_helper import db_helper
from core.models.user import User
from user.crud import get_user_by_username
from clients.redis.RedisClient import redis_client

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = settings.auth_jwt.algorithm

http_bearer = HTTPBearer()


async def validate_auth_user(
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    user = await get_user_by_username(username=username, session=session)

    if not user or not auth_utils.validate_password(password=password, hashed_password=user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid username or password')
    return user


async def get_current_user(
    session_id: str = Cookie(None),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    if session_id:
        user = redis_client.hgetall(f'session:{session_id}')
        if user:
            user['user_id'] = int(user['user_id'])
            return user


async def create_session(user_id: int, session_id: str, session: AsyncSession):
    new_session = SessionModel(user_id=user_id, session_id=session_id)
    session.add(new_session)
    await session.commit()


async def get_session(session_id: str, session: AsyncSession) -> User | None:
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await session.execute(stmt)
    session_model = result.scalar_one_or_none()

    if session_model:
        return await session.get(User, session_model.user_id)
    return None


async def delete_session(session_id: str, session: AsyncSession):
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await session.execute(stmt)
    session_model = result.scalar_one_or_none()

    if session_model:
        await session.delete(session_model)
        await session.commit()
