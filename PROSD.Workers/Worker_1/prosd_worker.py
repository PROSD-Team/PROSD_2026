import time
import json
import logging
import requests
import psycopg2
from psycopg2.extras import DictCursor
from minio import Minio
import yaml 
import io

# Налаштування формату логування для production-середовища
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("WorkerNode")

class WorkerNode:
    def __init__(self, gateway_meta_url, db_config, minio_config):
        self.gateway_meta_url = gateway_meta_url
        self.db_config = db_config
        self.minio_config = minio_config
        self.algorithms = {}

        # Ініціалізація клієнта MinIO для роботи з файловим сховищем
        self.storage = Minio(
            endpoint=self.minio_config.get("endpoint"),
            access_key=self.minio_config.get("access_key"),
            secret_key=self.minio_config.get("secret_key"),
            secure=self.minio_config.get("secure", False)
        )
        self.bucket_name = self.minio_config.get("bucket_name", "pipeline-runs")

    def algorithm(self, name, category, description, input_schema):
        """
        Декоратор для реєстрації бізнес-логіки алгоритму.
        Зберігає метадані та функцію-обробник для подальшого використання.
        """
        def decorator(func):
            metadata = {
                "id": f"python-{name}-worker",
                "name": name,
                "category": category,
                "description": description,
                "inputSchema": json.dumps(input_schema),
                "isActive": True
            }
            self.algorithms[name] = {
                "metadata": metadata,
                "handler": func
            }
            return func
        return decorator

    def _register_all_algorithms(self):
        """
        Відправляє метадані всіх зареєстрованих алгоритмів на API Gateway (.NET).
        Включає логіку повторних спроб (Retry) на випадок, якщо Gateway ще завантажується.
        """
        max_retries = 5
        for name, data in self.algorithms.items():
            registered = False
            for attempt in range(max_retries):
                logger.info(f"Registering algorithm: '{name}' (Attempt {attempt+1}/{max_retries})")
                try:
                    response = requests.post(
                        self.gateway_meta_url, 
                        json=data["metadata"],
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    response.raise_for_status()
                    logger.info(f"Algorithm '{name}' successfully registered.")
                    registered = True
                    break # Успішно зареєструвалися, виходимо з циклу
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Gateway is not ready yet: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
            
            if not registered:
                logger.error(f"Failed to register '{name}' after {max_retries} attempts.")

    def _get_db_connection(self):
        """Створює нове підключення до бази даних PostgreSQL."""
        return psycopg2.connect(**self.db_config)

    def start(self):
        """
        Головний цикл життєдіяльності воркера (Polling).
        Опитує базу даних на наявність нових завдань та передає їх на обробку.
        """
        logger.info("Starting Worker Node initialization...")
        self._register_all_algorithms()
        
        supported_workers = list(self.algorithms.keys())
        logger.info(f"Listening for tasks targeting: {supported_workers}")

        conn = None # Тримаємо підключення відкритим для економії ресурсів БД
        while True:
            try:
                # Відновлення підключення, якщо воно було втрачено
                if conn is None or conn.closed:
                    conn = self._get_db_connection()

                with conn.cursor(cursor_factory=DictCursor) as cur:
                    # Пошук першого доступного завдання для підтримуваних алгоритмів.
                    # Завантажуємо також PipelineSteps для маршрутизації (Routing Slip).
                    cur.execute("""
                        SELECT "Id", "TargetWorker", "S3FolderPath", "CurrentStepIndex", "PipelineSteps" 
                        FROM "Jobs" 
                        WHERE "Status" = 'pending' AND "TargetWorker" = ANY(%s) 
                        ORDER BY "CreatedAt" 
                        LIMIT 1 
                        FOR UPDATE SKIP LOCKED;
                    """, (supported_workers,))
                    
                    job = cur.fetchone()

                    if job:
                        job_id = job["Id"]
                        target_worker = job["TargetWorker"]
                        s3_folder = job["S3FolderPath"]
                        current_step = job["CurrentStepIndex"]
                        pipeline_steps = job["PipelineSteps"] or ""
                        
                        logger.info(f"Picked up JobId {job_id} for '{target_worker}'")

                        # Блокування завдання (зміна статусу на processing)
                        cur.execute('UPDATE "Jobs" SET "Status" = \'processing\', "StartedAt" = NOW() WHERE "Id" = %s', (job_id,))
                        conn.commit()

                        # Передача завдання в ізольований метод обробки
                        self._process_job(job_id, target_worker, s3_folder, current_step, pipeline_steps, cur, conn)
                    else:
                        # Завдань немає, просто підтверджуємо транзакцію і чекаємо
                        conn.commit()

            except psycopg2.OperationalError as db_err:
                logger.error(f"Database connection error: {db_err}. Reconnecting...")
                if conn and not conn.closed:
                    conn.close()
                conn = None # Форсуємо перепідключення на наступній ітерації
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
                if conn and not conn.closed:
                    conn.rollback()

            # Затримка перед наступним запитом до БД
            time.sleep(3)

    def _process_job(self, job_id, target_worker, s3_folder, current_step, pipeline_steps, cur, conn):
        """
        Ізольована логіка виконання конвеєра: завантаження даних з MinIO,
        виклик бізнес-логіки, збереження результатів та передача естафети.
        """
        try:
            parameters = {}
            
            if current_step == 0:
                # Перший крок: читаємо вхідні параметри від користувача з config.yaml
                config_path = f"{s3_folder}/config.yaml"
                response = self.storage.get_object(self.bucket_name, config_path)
                config_content = response.read().decode('utf-8')
                response.close()
                response.release_conn()

                # Безпечний парсинг YAML та JSON
                job_config = yaml.safe_load(config_content) or {}
                parameters_str = job_config.get('parameters_json', '{}')
                if parameters_str:
                    try:
                        parameters = json.loads(parameters_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse parameters_json for JobId {job_id}, proceeding with empty parameters.")
            else:
                # Наступні кроки: читаємо результати від попереднього алгоритму з output.json
                output_path = f"{s3_folder}/output.json"
                response = self.storage.get_object(self.bucket_name, output_path)
                output_content = response.read().decode('utf-8')
                response.close()
                response.release_conn()
                
                parameters = json.loads(output_content)

            # Виклик функції-обробника конкретного алгоритму
            handler_function = self.algorithms[target_worker]["handler"]
            result = handler_function(parameters)

            # Форматування та збереження результату в MinIO (перезаписує output.json)
            result_json = json.dumps(result, ensure_ascii=False).encode('utf-8')
            output_path = f"{s3_folder}/output.json"
            
            self.storage.put_object(
                self.bucket_name,
                output_path,
                data=io.BytesIO(result_json),
                length=len(result_json),
                content_type="application/json"
            )

            # --- ЕТАП 5: ROUTING SLIP (ПЕРЕДАЧА ЕСТАФЕТИ) ---
            steps_list = [s.strip() for s in pipeline_steps.split(',') if s.strip()]
            
            # Перевіряємо чи є ще кроки в масиві Pipeline_Steps
            if current_step < len(steps_list) - 1:
                # Наступний крок існує. Передаємо завдання наступному мікросервісу.
                next_step_index = current_step + 1
                next_worker = steps_list[next_step_index]
                
                cur.execute(
                    'UPDATE "Jobs" SET "CurrentStepIndex" = %s, "TargetWorker" = %s, "Status" = \'pending\' WHERE "Id" = %s',
                    (next_step_index, next_worker, job_id)
                )
                conn.commit()
                logger.info(f"Routing Slip: JobId {job_id} advanced to step {next_step_index} ({next_worker})")
            else:
                # Це був останній крок конвеєра. Встановлюємо фінальний статус.
                # Це автоматично запустить тригер NOTIFY у PostgreSQL.
                cur.execute('UPDATE "Jobs" SET "Status" = \'completed\' WHERE "Id" = %s', (job_id,))
                conn.commit()
                logger.info(f"JobId {job_id} fully completed (Pipeline finished).")

        except Exception as e:
            logger.error(f"Failed to process JobId {job_id}: {e}")
            conn.rollback() # Скасовуємо будь-які транзакції, якщо вони зависли
            
            # Спроба зберегти статус помилки (fallback)
            try:
                cur.execute('UPDATE "Jobs" SET "Status" = \'failed\' WHERE "Id" = %s', (job_id,))
                conn.commit()
            except Exception as inner_e:
                logger.error(f"Critical fallback failure: could not set JobId {job_id} to failed: {inner_e}")
                conn.rollback()