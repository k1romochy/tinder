from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth.crud import get_current_user
from core.models.db_helper import db_helper
from user.schemas import UserCreate, User
from user import crud as user


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/', response_model=list[User])
async def get_users(session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    return await user.get_users(session=session)


@router.get('/{user_id}/', response_model=User)
async def get_user(user_id: int,
                   session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    return await user.get_user_by_id(user_id=user_id, session=session)


@router.post('/registrate/', response_model=UserCreate)
async def register_user(user_in: UserCreate,
                        session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    try:
        return await user.registrate_user(user=user_in, session=session)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this email already exists')


@router.get('/show/me/', response_model=User)
async def show_me(current_user = Depends(get_current_user),
                  session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    user_id = current_user['user_id']
    return await user.get_me(user_id=user_id, session=session)

