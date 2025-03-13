import json
import logging
from confluent_kafka import Producer
from typing import Dict, Any

logger = logging.getLogger(__name__)

class KafkaProducer:
    """
    Класс для отправки сообщений в Kafka
    """
    def __init__(self, bootstrap_servers: str = 'kafka:9092'):
        """
        Инициализация Producer
        """
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'tinder-producer'
        })
    
    def produce(self, topic: str, key: str, value: Dict[str, Any]) -> None:
        """
        Отправка сообщения в Kafka
        
        Args:
            topic: Тема Kafka
            key: Ключ сообщения
            value: Значение сообщения в виде словаря
        """
        try:
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=json.dumps(value).encode('utf-8'),
                callback=self._delivery_report
            )
            # Принудительная отправка всех сообщений
            self.producer.flush()
            logger.info(f"Сообщение отправлено в топик {topic}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Kafka: {str(e)}")
    
    @staticmethod
    def _delivery_report(err, msg) -> None:
        """
        Callback-функция для отчетов о доставке сообщений
        """
        if err is not None:
            logger.error(f"Ошибка доставки сообщения: {err}")
        else:
            logger.info(f"Сообщение доставлено в {msg.topic()} [{msg.partition()}]")


kafka_producer = KafkaProducer() 