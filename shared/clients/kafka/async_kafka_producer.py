import json
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

class AsyncKafkaProducer:
    """
    Асинхронный класс для отправки сообщений в Kafka
    """
    def __init__(self, bootstrap_servers: str = 'kafka:9092'):
        """
        Инициализация Producer
        """
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'tinder-async-producer'
        })
        self._delivery_callbacks = {}
        self._running = True
        self._poll_task = None
    
    def start(self):
        """
        Запускает фоновую задачу для обработки ответов от Kafka
        """
        if self._poll_task is None:
            self._running = True
            self._poll_task = asyncio.create_task(self._poll_producer())
            logger.info("AsyncKafkaProducer started")
    
    async def stop(self):
        """
        Останавливает фоновую задачу и закрывает соединение
        """
        if self._poll_task is not None:
            self._running = False
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
            logger.info("AsyncKafkaProducer stopped")
    
    async def send(
        self, 
        topic: str, 
        value: bytes, 
        key: Optional[bytes] = None,
        on_delivery: Optional[Callable] = None,
        timeout: float = 10.0
    ) -> None:
        """
        Асинхронно отправляет сообщение в Kafka
        
        Args:
            topic: Тема Kafka
            value: Значение сообщения в виде байтов
            key: Ключ сообщения в виде байтов (опционально)
            on_delivery: Функция обратного вызова при доставке (опционально)
            timeout: Время ожидания в секундах для подтверждения доставки
        """
        # Убедиться, что фоновая задача запущена
        self.start()
        
        # Создаем future для отслеживания завершения отправки
        future = asyncio.Future()
        
        def delivery_callback(err, msg):
            """Внутренний callback для tracking completion"""
            if asyncio.get_event_loop().is_running():
                if err:
                    asyncio.create_task(self._handle_delivery_error(future, err, msg))
                else:
                    asyncio.create_task(self._handle_delivery_success(future, msg))
            
            # Вызвать дополнительный пользовательский callback, если предоставлен
            if on_delivery:
                on_delivery(err, msg)
        
        try:
            # Отправляем сообщение (это блокирующий вызов, но обычно очень быстрый)
            await asyncio.to_thread(
                self.producer.produce,
                topic=topic,
                value=value,
                key=key,
                callback=delivery_callback
            )
            
            # Ждем подтверждения доставки сообщения
            try:
                await asyncio.wait_for(future, timeout=timeout)
                logger.info(f"Сообщение успешно отправлено в топик {topic}")
                return True
            except asyncio.TimeoutError:
                logger.error(f"Таймаут при ожидании подтверждения доставки в топик {topic}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Kafka: {str(e)}")
            raise
    
    async def _poll_producer(self):
        """
        Фоновая задача для опроса продюсера на получение ответов
        """
        while self._running:            
            await asyncio.to_thread(self.producer.poll, 0.1)
            
            await asyncio.sleep(0.01)
    
    async def _handle_delivery_success(self, future, msg):
        """Обрабатывает успешную доставку сообщения"""
        if not future.done():
            future.set_result(True)
            logger.info(f"Сообщение доставлено: {msg.topic()} [{msg.partition()}] offset {msg.offset()}")
    
    async def _handle_delivery_error(self, future, err, msg):
        """Обрабатывает ошибку доставки сообщения"""
        if not future.done():
            future.set_exception(Exception(f"Ошибка доставки: {err}"))
            logger.error(f"Ошибка доставки сообщения: {err}")
    
    async def flush(self, timeout: float = 10.0):
        """
        Асинхронно отправляет все сообщения из буфера и ждет подтверждения
        
        Args:
            timeout: Время ожидания в секундах для отправки всех сообщений
        """
        await asyncio.to_thread(self.producer.flush, timeout)
        logger.info("Producer buffer flushed")


async_kafka_producer = AsyncKafkaProducer()

async def kafka_send_message(topic: str, value: Dict[str, Any], key: str = None):
    """
    Отправляет сообщение в Kafka с сериализацией значения в JSON
    
    Args:
        topic: Тема Kafka
        value: Значение сообщения в виде словаря (будет преобразовано в JSON)
        key: Ключ сообщения (опционально)
    """
    serialized_value = json.dumps(value).encode('utf-8')
    serialized_key = key.encode('utf-8') if key else None
    
    return await async_kafka_producer.send(
        topic=topic,
        value=serialized_value,
        key=serialized_key
    ) 