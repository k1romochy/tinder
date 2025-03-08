from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth.crud import get_current_user_id
from core.models.db_helper import db_helper
from user.schemas import UserCreate, User, UserModel, Photo, UserCreateResponse
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
async def register_user(user_in: UserCreateResponse,
                        session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    try:
        return await user.registrate_user(user=user_in, session=session)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this email already exists')


@router.get('/show/me/', response_model=UserModel)
async def show_me(user_id = Depends(get_current_user_id),
                  session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация"
        )
        
    return await user.get_me(user_id=user_id, session=session)


@router.post('/registrate/upload_photo/')
async def upload_photography(
    user_id = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    file: UploadFile = File()
):
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация"
        )
    
    result = await user.upload_photo(user_id=user_id, session=session, file=file)
    return result
