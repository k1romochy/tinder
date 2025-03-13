import asyncio
import logging
import os
from typing import Dict, List, Tuple, Callable, Coroutine, Any
from clients.kafka.async_kafka_consumer import AsyncKafkaConsumer

logger = logging.getLogger(__name__)

class KafkaManager:
    """Менеджер для управления несколькими Kafka консумерами"""
    
    def __init__(self):
        self.consumers: Dict[str, Tuple[AsyncKafkaConsumer, asyncio.Task]] = {}
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    
    async def add_consumer(self, 
                         topic: str, 
                         group_id: str, 
                         handler: Callable[[Dict[str, Any]], Coroutine],
                         consumer_id: str = None) -> str:
        """
        Добавляет и запускает новый консумер
        
        Args:
            topic: Топик Kafka
            group_id: ID группы консумеров
            handler: Асинхронная функция-обработчик сообщений
            consumer_id: Опциональный ID для консумера (если не указан, генерируется автоматически)
            
        Returns:
            ID консумера
        """
        if consumer_id is None:
            consumer_id = f"{topic}_{group_id}_{len(self.consumers)}"
            
        # Проверяем, не существует ли уже консумер с таким ID
        if consumer_id in self.consumers:
            logger.warning(f"Консумер с ID {consumer_id} уже существует")
            return consumer_id
            
        # Создаем новый консумер
        consumer = AsyncKafkaConsumer(
            topic=topic, 
            group_id=group_id,
            bootstrap_servers=self.bootstrap_servers
        )
        
        # Запускаем обработку в отдельной задаче
        task = asyncio.create_task(consumer.consume(handler))
        
        # Сохраняем консумер и задачу
        self.consumers[consumer_id] = (consumer, task)
        
        logger.info(f"Запущен консумер {consumer_id} для топика {topic}, группа {group_id}")
        return consumer_id
        
    async def remove_consumer(self, consumer_id: str) -> bool:
        """
        Останавливает и удаляет консумер
        
        Args:
            consumer_id: ID консумера для удаления
            
        Returns:
            True, если консумер был удален успешно
        """
        if consumer_id not in self.consumers:
            logger.warning(f"Консумер с ID {consumer_id} не найден")
            return False
            
        consumer, task = self.consumers[consumer_id]
        
        # Останавливаем консумер
        consumer.stop()
        
        # Ждем завершения задачи
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"Таймаут при остановке консумера {consumer_id}")
            task.cancel()
            
        # Удаляем консумер из словаря
        del self.consumers[consumer_id]
        
        logger.info(f"Консумер {consumer_id} остановлен и удален")
        return True
        
    async def stop_all(self):
        """Останавливает все консумеры"""
        consumer_ids = list(self.consumers.keys())
        for consumer_id in consumer_ids:
            await self.remove_consumer(consumer_id)
            
        logger.info("Все консумеры остановлены")

# Создаем глобальный экземпляр менеджера
kafka_manager = KafkaManager() 