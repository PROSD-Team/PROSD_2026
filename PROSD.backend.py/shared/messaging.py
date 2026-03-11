"""
Абстракція для споживання повідомлень з RabbitMQ.
Інтегрує AOP-декоратори логування та загальну обробку помилок черги.
"""
import os
import json
import traceback
import aio_pika
from typing import Callable, Awaitable
from pydantic import ValidationError

from shared.aspects import log_execution, get_logger
from shared.contracts import JobMessage

# Читаємо URL для підключення з середовища (задається в docker-compose.yml)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

class RabbitMQWorker:
    def __init__(self, queue_name: str, service_name: str):
        self.queue_name = queue_name
        self.service_name = service_name
        self.logger = get_logger(service_name)

    async def start_consuming(self, handler: Callable[[JobMessage], Awaitable[None]]):
        """
        Підключається до RabbitMQ та починає слухати чергу.
        handler - це ваша асинхронна функція з бізнес-логікою.
        """
        # connect_robust автоматично відновлює з'єднання при розривах
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        # Створюємо чергу, якщо вона ще не існує (durable=True означає, що вона переживе рестарт брокера)
        queue = await channel.declare_queue(self.queue_name, durable=True)
        
        self.logger.info(json.dumps({"event": "WORKER_STARTED", "queue": self.queue_name,
            "message": "Підключено до RabbitMQ. Очікування задач..."
        }))

        # Починаємо споживати повідомлення
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # message.process() автоматично надсилає ACK (успіх) або NACK (помилка) в RabbitMQ
                async with message.process(): 
                    await self._process_message(message.body.decode('utf-8'), handler)

    # Застосовуємо наш AOP-аспект для логування кожної задачі з черги
    @log_execution(service_name="rabbitmq-consumer", include_args=False)
    async def _process_message(self, raw_body: str, handler: Callable[[JobMessage], Awaitable[None]]):
        """
        Парсить JSON, валідує контракт і викликає бізнес-логіку.
        """
        try:
            # Десеріалізація та строга валідація через Pydantic
            data = json.loads(raw_body)
            job_message = JobMessage(**data)
            
            # Виклик самого алгоритму (хендлера)
            await handler(job_message)
            
        except ValidationError as e:
            # Помилка валідації вхідного контракту
            self.logger.error(json.dumps({"event": "VALIDATION_ERROR", "error": str(e),
                "message": "Отримано некоректне повідомлення з черги."
            }))
        except Exception as e:
            # Глобальне перехоплення критичних помилок щоб воркер не впав
            tb = traceback.format_exc()
            self.logger.error(json.dumps({"event": "CRITICAL_ERROR", "error": str(e), "trace": tb[-500:],
                "message": "Виникла помилка під час виконання алгоритму."
            }))