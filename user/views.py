from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth.crud import get_current_user_id
from shared.core.models.db_helper import db_helper
from user.schemas import UserCreate, User, UserModel, Photo, UserCreateResponse, UserShowMe
from user import crud as user
from auth.jwt_auth import auth_user_jwt


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/', response_model=list[User])
async def get_users(session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    return await user.get_users(session=session)


@router.get('/{user_id}/', response_model=User)
async def get_user(user_id: int,
                   session: AsyncSession = Depends(db_helper.scoped_session_dependency)):
    return await user.get_user_by_id(user_id=user_id, session=session)


@router.post('/registrate/', response_model=dict)
async def register_user(
    user_in: UserCreate,
    response: Response,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    try:
        new_user = await user.registrate_user(user=user_in, session=session)
        
        token = await auth_user_jwt(
            response=response,
            username=user_in.username,
            password=user_in.password,
            session=session
        )
        
        return {
            'user': new_user,
            'token': token
        }
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this email already exists')


@router.get('/show/me/', response_model=UserShowMe)
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
