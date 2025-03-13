from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing import List, Dict, Any

from auth.crud import get_current_user_id
from shared.core.models.db_helper import db_helper
from user.schemas import UserCreate, User, UserModel, Photo
from stack_partners import crud as prt
from shared.clients.redis.RedisClient import redis_cache
from stack_partners.tasks import _get_recommendations_for_user


router = APIRouter(prefix='/stack', tags=['Stack'])


@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_recommendations(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.get_session),
):
    cache_key = f"user:{current_user_id}:recommendations"
    
    cached_recommendations = redis_cache.get(cache_key)
    
    if cached_recommendations:
        return cached_recommendations
    
    recommendations = await _get_recommendations_for_user(session, current_user_id)
    
    if not recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рекомендации не найдены"
        )
    
    redis_cache.set(cache_key, recommendations, expiration=3600)
    
    return recommendations



