import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Form, HTTPException, Response, Cookie
from auth import utils as auth_utils
from auth import crud as auth_crud
from shared.core.models.db_helper import db_helper
from auth.jwt_model import Token
from user import crud as user_crud
from user.schemas import UserModel
from shared.clients.redis.RedisClient import redis_client
from fastapi import status

router = APIRouter(prefix='/auth', tags=['auth'])
COOKIE_SESSION_ID_KEY = 'session_id'


@router.post("/login/", response_model=Token)
async def auth_user_jwt(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    user = await user_crud.get_user_by_username(username=username, session=session)

    if not user or not auth_utils.validate_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    jwt_payload = {"sub": user.username, "user_id": user.id, "email": user.email}
    token = auth_utils.encode_jwt(jwt_payload)

    session_id = str(uuid.uuid4())
    await auth_crud.create_session(user.id, session_id, session)
    await redis_client.hset(f'session:{session_id}', mapping={'username': f'{user.username}',
                                                        'user_id': user.id,
                                                        'email': f'{user.email}'})

    response.set_cookie(key=COOKIE_SESSION_ID_KEY, value=session_id, httponly=True, secure=False, samesite='lax')

    return Token(access_token=token, token_type="Bearer")

async def get_current_user_dependency(
    session_id: str = Cookie(None),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    from auth.crud import get_current_user
    return await get_current_user(session_id=session_id, session=session)



@router.get('/me/')
async def get_me(current_user = Depends(get_current_user_dependency)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация"
        )
        
    return {
        'username': current_user["username"],
        'user_id': current_user["user_id"]
    }


@router.post("/logout/")
async def logout(
        response: Response,
        session_id: str = Cookie(None),
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):

    if session_id:
        await auth_crud.delete_session(session_id, session)
        user_id = await redis_client.hget(f'session:{session_id}', "user_id")
        await redis_client.delete(f'session:{session_id}')
        await redis_client.delete(f'user:{user_id}')

    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}

