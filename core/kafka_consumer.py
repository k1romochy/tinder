import json
import logging
from typing import Callable, Dict, Any
from confluent_kafka import Consumer, KafkaError

logger = logging.getLogger(__name__)

class KafkaConsumer:
    """
    Класс для потребления сообщений из Kafka
    """
    def __init__(
        self, 
        topic: str, 
        group_id: str, 
        bootstrap_servers: str = 'kafka:9092',
        auto_offset_reset: str = 'earliest'
    ):
        """
        Инициализация Consumer
        
        Args:
            topic: Тема Kafka
            group_id: ID группы потребителей
            bootstrap_servers: Адрес серверов Kafka
            auto_offset_reset: Стратегия сброса смещения
        """
        self.topic = topic
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': True
        })
        self.consumer.subscribe([topic])
        logger.info(f"Подписка на топик {topic} с group_id {group_id}")
    
    def consume(self, message_handler: Callable[[Dict[str, Any]], None], poll_timeout: float = 1.0) -> None:
        """
        Начать потребление сообщений
        
        Args:
            message_handler: Функция обработки сообщений
            poll_timeout: Время ожидания новых сообщений в секундах
        """
        try:
            while True:
                msg = self.consumer.poll(poll_timeout)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"Достигнут конец раздела для {msg.topic()} [{msg.partition()}]")
                    else:
                        logger.error(f"Ошибка: {msg.error()}")
                    continue
                
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    message_handler(value)
                    logger.info(f"Обработано сообщение из {msg.topic()} [{msg.partition()}] offset {msg.offset()}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения: {str(e)}")
                    
        except KeyboardInterrupt:
            logger.info("Завершение работы потребителя")
        finally:
            self.consumer.close()
            logger.info("Потребитель закрыт") 
            