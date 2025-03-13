import json
import logging
import asyncio
from typing import Callable, Dict, Any, Coroutine
from confluent_kafka import Consumer, KafkaError

logger = logging.getLogger(__name__)

class AsyncKafkaConsumer:
    """
    Асинхронный класс для потребления сообщений из Kafka
    """
    def __init__(
        self, 
        topic: str, 
        group_id: str, 
        bootstrap_servers: str = 'kafka:9092',
        auto_offset_reset: str = 'earliest'
    ):
        self.topic = topic
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': True
        })
        self.consumer.subscribe([topic])
        logger.info(f"Подписка на топик {topic} с group_id {group_id}")
        self._running = False
    
    async def consume(self, message_handler: Callable[[Dict[str, Any]], Coroutine], 
                      poll_timeout: float = 1.0) -> None:
        """
        Начать асинхронное потребление сообщений
        
        Args:
            message_handler: Асинхронная функция обработки сообщений
            poll_timeout: Время ожидания новых сообщений в секундах
        """
        self._running = True
        try:
            while self._running:
                # Опрос Kafka выполняется в отдельном потоке, чтобы не блокировать event loop
                msg = await asyncio.to_thread(self.consumer.poll, poll_timeout)
                
                if msg is None:
                    # Даем шанс другим корутинам выполниться
                    await asyncio.sleep(0.01)
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"Достигнут конец раздела для {msg.topic()} [{msg.partition()}]")
                    else:
                        logger.error(f"Ошибка: {msg.error()}")
                    continue
                
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    # Асинхронно обрабатываем сообщение
                    await message_handler(value)
                    logger.info(f"Обработано сообщение из {msg.topic()} [{msg.partition()}] offset {msg.offset()}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        
        finally:
            self.consumer.close()
            logger.info("Потребитель закрыт")
    
    def stop(self):
        """Остановить потребление сообщений"""
        self._running = False 