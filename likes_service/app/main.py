import asyncio
import logging
import os
from shared.clients.kafka.kafka_manager import kafka_manager
from likes_service.handlers.like_handlers import handle_user_like, handle_user_unlike


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


LIKE_SERVICE_GROUP_ID = "likes_service"


USER_LIKES_TOPIC = "user_likes"
USER_UNLIKES_TOPIC = "user_unlikes"
USER_MATCHES_TOPIC = "user_matches"

async def setup_and_run():
    logger.info("Запуск сервиса лайков...")
    
    await kafka_manager.add_consumer(
        topic=USER_LIKES_TOPIC,
        group_id=LIKE_SERVICE_GROUP_ID,
        handler=handle_user_like,
        consumer_id="like_consumer"
    )
    
    await kafka_manager.add_consumer(
        topic=USER_UNLIKES_TOPIC,
        group_id=LIKE_SERVICE_GROUP_ID,
        handler=handle_user_unlike,
        consumer_id="unlike_consumer"
    )
    
    logger.info("Сервис лайков успешно запущен и ожидает сообщений")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await kafka_manager.stop_all()
        logger.info("Сервис лайков остановлен")

if __name__ == "__main__":
    asyncio.run(setup_and_run()) 