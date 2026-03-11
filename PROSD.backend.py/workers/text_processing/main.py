"""
Точка входу для мікросервісу Text Processing.
Слухає RabbitMQ, виконує алгоритм, зберігає результати в MinIO, оновлює БД.
"""
import sys
import os
import asyncio

# Додаємо корінь проєкту до PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from shared.messaging import RabbitMQWorker
from shared.contracts import JobMessage
from shared.storage import save_job_output
from shared.database import update_job_status
from shared.aspects import get_logger, AlgorithmError

from workers.text_processing.algorithm import preprocess_text

SERVICE_NAME = "text-processing"
QUEUE_NAME = "q_text_processing"
logger = get_logger(SERVICE_NAME)

async def text_processing_handler(job: JobMessage):
    """
    Хендлер, який викликається для кожного повідомлення з черги RabbitMQ.
    """
    logger.info(f"[{job.job_id}] Початок обробки задачі...")
    
    # 1. Оновлюємо статус у БД на "В процесі"
    await update_job_status(job.job_id, status="Processing")
    
    try:
        # 2. Витягуємо параметри та запускаємо алгоритм
        text = job.parameters.get("text", "")
        lowercase = job.parameters.get("lowercase", True)
        remove_punctuation = job.parameters.get("remove_punctuation", True)
        
        # Алгоритм автоматично закешований та залогований (AOP)
        stats = await preprocess_text(text, lowercase, remove_punctuation)
        
        # Виділяємо великі дані (наприклад, сам очищений текст) в окремий файл
        processed_text = stats.pop("processed_text")
        large_files = {"clean_text.txt": processed_text.encode('utf-8')}
        
        # 3. Зберігаємо результати у сховище (MinIO або локально)
        folder_path, output_results = save_job_output(
            category=job.category,
            algorithm=job.algorithm,
            job_id=job.job_id,
            parameters=job.parameters,
            results=stats,
            large_files=large_files
        )
        
        # 4. Оновлюємо статус у БД на "Успішно"
        await update_job_status(job.job_id, status="Completed", output_folder=folder_path)
        logger.info(f"[{job.job_id}] Успішно завершено. Дані в: {folder_path}")

    except Exception as exc:
        # Якщо сталася помилка (валідація або алгоритм), оновлюємо БД
        await update_job_status(job.job_id, status="Failed", error_message=str(exc))
        # Перекидаємо виняток далі, щоб RabbitMQWorker його залогував (AOP error aspect)
        raise AlgorithmError(f"Задача {job.job_id} завершилась з помилкою: {exc}")

async def main():
    logger.info(f"Запуск мікросервісу {SERVICE_NAME}...")
    worker = RabbitMQWorker(queue_name=QUEUE_NAME, service_name=SERVICE_NAME)
    
    # Блокуючий виклик: слухаємо чергу безкінечно
    await worker.start_consuming(text_processing_handler)

if __name__ == "__main__":
    asyncio.run(main())