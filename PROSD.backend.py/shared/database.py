"""
Модуль для асинхронної роботи з PostgreSQL.
Використовується воркерами для оновлення статусу задачі після виконання.
"""
import os
import json
import asyncpg
from shared.aspects import log_execution, get_logger

DB_DSN = os.getenv("DATABASE_URL", "postgresql://linglab:linglab@localhost:5432/linglab")
logger = get_logger("database")

@log_execution(service_name="database", include_args=True)
async def update_job_status(job_id: str, status: str, output_folder: str = None, error_message: str = None):
    """
    Оновлює запис у таблиці Jobs (яку попередньо створив API Gateway).
    Статуси: 'Processing', 'Completed', 'Failed'.
    """
    try:
        conn = await asyncpg.connect(DB_DSN)
        query = """
            UPDATE jobs 
            SET status = $1, 
                output_folder = $2, 
                error_message = $3, 
                updated_at = NOW() 
            WHERE id = $4
        """
        await conn.execute(query, status, output_folder, error_message, job_id)
        await conn.close()
    except Exception as e:
        logger.error(json.dumps({
            "event": "DB_UPDATE_ERROR",
            "job_id": job_id,
            "error": str(e)
        }))
        # Ми не викидаємо виняток далі, щоб не зламати процес підтвердження RabbitMQ (ACK),
        # оскільки сама задача вже виконана (або зафейлилась) коректно.