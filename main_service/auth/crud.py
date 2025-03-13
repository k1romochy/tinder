import os

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Form, HTTPException, status, Cookie
from fastapi.security import HTTPBearer

from auth import utils as auth_utils
from shared.core.config import settings
from shared.core.models import SessionModel
from shared.core.models.db_helper import db_helper
from shared.core.models.user import User
from user.crud import get_user_by_username
from shared.clients.redis.RedisClient import redis_client

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


async def get_current_user_id(
    session_id: str = Cookie(None),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    if session_id:
        user = await redis_client.hgetall(f'session:{session_id}')
        if user and 'user_id' in user:
            try:
                return int(user['user_id'])
            except ValueError:
                result = await session.execute(select(User).where(User.username == user.get('username')))
                db_user = result.scalar_one_or_none()
                if db_user:
                    await redis_client.hset(f'session:{session_id}', mapping={'user_id': db_user.id})
                    return db_user.id
                return None
        else:
            try:
                user_id = int(session_id)
                result = await session.execute(select(User).where(User.id == user_id))
            except ValueError:
                result = await session.execute(select(User).where(User.id == session_id))
            
            user = result.scalar_one_or_none()
            if user:
                await redis_client.hset(f'session:{session_id}', mapping={'user_id': user.id})
                return user.id
            else:
                return None


async def get_current_user(
    session_id: str = Cookie(None),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    if session_id:
        redis_user = await redis_client.hgetall(f'session:{session_id}')
        if redis_user and 'user_id' in redis_user:
            return {
                'user_id': int(redis_user['user_id']),
                'username': redis_user.get('username', ''),
                'email': redis_user.get('email', '')
            }
        
        user_id = await get_current_user_id(session_id=session_id, session=session)
        if user_id:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email
                }
                await redis_client.hset(f'session:{session_id}', mapping=user_data)
                return user_data
    
    return None


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
