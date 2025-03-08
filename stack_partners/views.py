from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth.crud import get_current_user_id
from core.models.db_helper import db_helper
from user.schemas import UserCreate, User, UserModel, Photo
from stack_partners import crud as prt


router = APIRouter(prefix='/stack', tags=['Stack'])



