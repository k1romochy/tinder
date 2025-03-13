import logging
import json
from typing import Dict, Any
import asyncio
from datetime import datetime
from sqlalchemy import select

from shared.clients.kafka.kafka_producer import KafkaProducer
from shared.core.models.db_helper import db_helper
from shared.core.models.user import User
from shared.core.models.like import Like, Match

logger = logging.getLogger(__name__)

kafka_producer = KafkaProducer(bootstrap_servers='kafka:9092')

USER_MATCHES_TOPIC = "user_matches"

async def handle_user_like(message: Dict[str, Any]) -> None:
    """
    Обработчик события лайка пользователя
    
    Args:
        message: Сообщение с данными о лайке
    """
    try:
        from_user_id = message.get("from_user_id")
        to_user_id = message.get("to_user_id")
        timestamp = message.get("timestamp", datetime.now().isoformat())
        
        if not from_user_id or not to_user_id:
            logger.error(f"Неверный формат сообщения для лайка: {message}")
            return
            
        logger.info(f"Обработка лайка от пользователя {from_user_id} к пользователю {to_user_id}")
        
        async with db_helper.get_session() as session:
            # Проверяем, существует ли уже лайк
            stmt = select(Like).where(
                Like.from_user_id == from_user_id,
                Like.to_user_id == to_user_id,
                Like.is_active == True
            )
            existing_like = await session.execute(stmt)
            existing_like = existing_like.scalar_one_or_none()
            
            if existing_like:
                logger.info(f"Лайк от {from_user_id} к {to_user_id} уже существует")
                return
                
            # Создаем новый лайк
            new_like = Like(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                created_at=datetime.now(),
                is_active=True
            )
            session.add(new_like)
            
            # Проверяем наличие взаимного лайка
            reverse_like_stmt = select(Like).where(
                Like.from_user_id == to_user_id,
                Like.to_user_id == from_user_id,
                Like.is_active == True
            )
            reverse_like = await session.execute(reverse_like_stmt)
            reverse_like = reverse_like.scalar_one_or_none()
            
            if reverse_like:
                logger.info(f"Обнаружен взаимный лайк между {from_user_id} и {to_user_id}")
                
                # Создаем матч (с меньшим ID первым)
                user1_id = min(from_user_id, to_user_id)
                user2_id = max(from_user_id, to_user_id)
                
                match_id = f"{user1_id}_{user2_id}"
                
                # Проверяем, существует ли уже матч
                match_stmt = select(Match).where(
                    Match.user1_id == user1_id,
                    Match.user2_id == user2_id
                )
                existing_match = await session.execute(match_stmt)
                existing_match = existing_match.scalar_one_or_none()
                
                if not existing_match:
                    # Создаем новый матч
                    new_match = Match(
                        user1_id=user1_id,
                        user2_id=user2_id,
                        created_at=datetime.now(),
                        is_active=True
                    )
                    session.add(new_match)
                    
                    # Создаем событие матча
                    match_event = {
                        "match_id": match_id,
                        "user1_id": from_user_id,
                        "user2_id": to_user_id,
                        "timestamp": timestamp,
                        "status": "new"
                    }
                    
                    # Сохраняем изменения
                    await session.commit()
                    
                    # Отправляем событие матча
                    await kafka_producer.send(
                        topic=USER_MATCHES_TOPIC,
                        value=json.dumps(match_event).encode('utf-8')
                    )
                    
                    logger.info(f"Отправлено событие матча: {match_id}")
                else:
                    logger.info(f"Матч между {user1_id} и {user2_id} уже существует")
                    await session.commit()
            else:
                logger.info(f"Взаимный лайк не обнаружен, сохранение лайка в базе данных")
                await session.commit()
            
    except Exception as e:
        logger.exception(f"Ошибка при обработке лайка: {str(e)}")


async def handle_user_unlike(message: Dict[str, Any]) -> None:
    """
    Обработчик события отмены лайка
    
    Args:
        message: Сообщение с данными об отмене лайка
    """
    try:
        from_user_id = message.get("from_user_id")
        to_user_id = message.get("to_user_id")
        
        if not from_user_id or not to_user_id:
            logger.error(f"Неверный формат сообщения для отмены лайка: {message}")
            return
            
        logger.info(f"Обработка отмены лайка от пользователя {from_user_id} к пользователю {to_user_id}")
        
        async with db_helper.get_session() as session:
            # Находим активный лайк
            stmt = select(Like).where(
                Like.from_user_id == from_user_id,
                Like.to_user_id == to_user_id,
                Like.is_active == True
            )
            like = await session.execute(stmt)
            like = like.scalar_one_or_none()
            
            if like:
                # Деактивируем лайк
                like.is_active = False
                
                # Проверяем наличие матча
                user1_id = min(from_user_id, to_user_id)
                user2_id = max(from_user_id, to_user_id)
                
                match_stmt = select(Match).where(
                    Match.user1_id == user1_id,
                    Match.user2_id == user2_id,
                    Match.is_active == True
                )
                match = await session.execute(match_stmt)
                match = match.scalar_one_or_none()
                
                if match:
                    # Деактивируем матч
                    match.is_active = False
                    logger.info(f"Деактивирован матч между {user1_id} и {user2_id}")
                
                await session.commit()
                logger.info(f"Лайк от {from_user_id} к {to_user_id} деактивирован")
            else:
                logger.info(f"Активный лайк от {from_user_id} к {to_user_id} не найден")
        
    except Exception as e:
        logger.exception(f"Ошибка при обработке отмены лайка: {str(e)}")


async def check_mutual_like(session, from_user_id: int, to_user_id: int) -> bool:
    """
    Проверяет, существует ли взаимный лайк между пользователями
    
    Args:
        session: Сессия базы данных
        from_user_id: ID пользователя, который поставил лайк
        to_user_id: ID пользователя, которому поставили лайк
        
    Returns:
        True, если существует взаимный лайк, False в противном случае
    """
    stmt = select(Like).where(
        Like.from_user_id == to_user_id,
        Like.to_user_id == from_user_id,
        Like.is_active == True
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None 