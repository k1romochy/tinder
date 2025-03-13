import asyncio
import logging
from typing import List, Dict, Any

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.models.db_helper import db_helper
from shared.clients.kafka.kafka_producer import kafka_producer
from shared.clients.redis.RedisClient import redis_cache
from stack_partners import crud

from stack_partners.schemas import UserRecomendationResponse

logger = logging.getLogger(__name__)


@shared_task(name="stack_partners.tasks.generate_user_recommendations")
def generate_user_recommendations():
    logger.info("Начало генерации рекомендаций для всех пользователей")
    
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_generate_user_recommendations_async())
    
    logger.info(f"Сгенерированы рекомендации для {result} пользователей")
    return result


async def _generate_user_recommendations_async() -> int:
    async with db_helper.scoped_session_dependency() as session:
        users = await _get_all_users(session)
        
        count = 0
        for user_id in users:
            try:
                recommended_users = await _get_recommendations_for_user(session, user_id)
                
                if recommended_users:
                    cache_key = f"user:{user_id}:recommendations"
                    redis_cache.set(cache_key, recommended_users, expiration=86400)
                    
                    kafka_producer.produce(
                        topic="user_recommendations",
                        key=str(user_id),
                        value={
                            "user_id": user_id,
                            "recommendations_count": len(recommended_users),
                            "cache_key": cache_key
                        }
                    )
                    
                    count += 1
                    logger.info(f"Сгенерированы рекомендации для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка при генерации рекомендаций для пользователя {user_id}: {str(e)}")
        
        return count


async def _get_all_users(session: AsyncSession) -> List[int]:
    pass


async def _get_recommendations_for_user(session: AsyncSession, user_id: int) -> List[UserRecomendationResponse]:
    result = []
    for nearby_id in nearby_user_ids:
        result.append(UserRecomendationResponse(
            id=nearby_id,
            name=f"User {nearby_id}",
            age=25,
            photos=["url1", "url2"]
        ))
    
    return result 
