import time
import json
import logging
import threading
import requests
import psycopg2
from psycopg2.extras import DictCursor
from minio import Minio
import yaml
import io
import os
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import logging_loki

# Prometheus metrics
JOBS_PROCESSED = Counter('worker_jobs_processed_total', 'Total jobs processed', ['worker', 'status'])
JOB_DURATION = Histogram('worker_job_duration_seconds', 'Job processing duration', ['worker'])
JOBS_IN_PROGRESS = Gauge('worker_jobs_in_progress', 'Jobs currently being processed', ['worker'])

class WorkerNode:
    def __init__(self, gateway_meta_url, db_config, minio_config):
        self.gateway_meta_url = gateway_meta_url
        self.db_config = db_config
        self.minio_config = minio_config
        self.algorithms = {}

        # MinIO client
        self.storage = Minio(
            endpoint=self.minio_config.get("endpoint"),
            access_key=self.minio_config.get("access_key"),
            secret_key=self.minio_config.get("secret_key"),
            secure=self.minio_config.get("secure", False)
        )
        self.bucket_name = self.minio_config.get("bucket_name", "pipeline-runs")

        self._setup_logging()
        self._start_metrics_server()

    def _setup_logging(self):
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        enable_logging = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
        loki_url = os.getenv("LOKI_URL", "http://loki:3100")
        worker_name = os.getenv("WORKER_NAME", "unknown-worker")

        self.logger = logging.getLogger(f"Worker.{worker_name}")
        self.logger.setLevel(log_level)

        # Console handler (JSON format)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        ))
        self.logger.addHandler(console_handler)

        if enable_logging:
            try:
                loki_handler = logging_loki.LokiHandler(
                    url=f"{loki_url}/loki/api/v1/push",
                    tags={"app": "worker", "worker": worker_name},
                    version="1",
                )
                self.logger.addHandler(loki_handler)
                self.logger.info(f"Loki logging enabled at {loki_url}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Loki handler: {e}")

    def _start_metrics_server(self):
        metrics_port = int(os.getenv("METRICS_PORT", "8000"))
        def run_metrics():
            start_http_server(metrics_port)
            self.logger.info(f"Metrics server started on port {metrics_port}")
        thread = threading.Thread(target=run_metrics, daemon=True)
        thread.start()

    def algorithm(self, name, category, description, input_schema):
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
        max_retries = 5
        for name, data in self.algorithms.items():
            registered = False
            for attempt in range(max_retries):
                self.logger.info(f"Registering algorithm: '{name}' (Attempt {attempt+1}/{max_retries})")
                try:
                    response = requests.post(
                        self.gateway_meta_url,
                        json=data["metadata"],
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    response.raise_for_status()
                    self.logger.info(f"Algorithm '{name}' successfully registered.")
                    registered = True
                    break
                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"Gateway not ready: {e}. Retrying in 5s...")
                    time.sleep(5)
            if not registered:
                self.logger.error(f"Failed to register '{name}' after {max_retries} attempts.")

    def _get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def start(self):
        self.logger.info("Starting Worker Node initialization...")
        self._register_all_algorithms()
        supported_workers = list(self.algorithms.keys())
        self.logger.info(f"Listening for tasks targeting: {supported_workers}")

        conn = None
        while True:
            try:
                if conn is None or conn.closed:
                    conn = self._get_db_connection()

                with conn.cursor(cursor_factory=DictCursor) as cur:
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
                        
                        self.logger.info(f"Picked up JobId {job_id} for '{target_worker}'")
                        cur.execute('UPDATE "Jobs" SET "Status" = \'processing\', "StartedAt" = NOW() WHERE "Id" = %s', (job_id,))
                        conn.commit()

                        self._process_job(job_id, target_worker, s3_folder, current_step, pipeline_steps, cur, conn)
                    else:
                        conn.commit()
            except psycopg2.OperationalError as db_err:
                self.logger.error(f"Database connection error: {db_err}. Reconnecting...")
                if conn and not conn.closed:
                    conn.close()
                conn = None
            except Exception as e:
                self.logger.error(f"Unexpected error in worker loop: {e}")
                if conn and not conn.closed:
                    conn.rollback()
            time.sleep(3)

    def _process_job(self, job_id, target_worker, s3_folder, current_step, pipeline_steps, cur, conn):
        worker_name = os.getenv("WORKER_NAME", target_worker)
        JOBS_IN_PROGRESS.labels(worker=worker_name).inc()
        start_time = time.time()
        status = "failed"
        try:
            parameters = {}
            if current_step == 0:
                config_path = f"{s3_folder}/config.yaml"
                response = self.storage.get_object(self.bucket_name, config_path)
                config_content = response.read().decode('utf-8')
                response.close()
                response.release_conn()
                job_config = yaml.safe_load(config_content) or {}
                parameters_str = job_config.get('parameters_json', '{}')
                if parameters_str:
                    try:
                        parameters = json.loads(parameters_str)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse parameters_json for JobId {job_id}")
            else:
                output_path = f"{s3_folder}/output.json"
                response = self.storage.get_object(self.bucket_name, output_path)
                output_content = response.read().decode('utf-8')
                response.close()
                response.release_conn()
                parameters = json.loads(output_content)

            handler_function = self.algorithms[target_worker]["handler"]
            result = handler_function(parameters)

            result_json = json.dumps(result, ensure_ascii=False).encode('utf-8')
            output_path = f"{s3_folder}/output.json"
            self.storage.put_object(
                self.bucket_name,
                output_path,
                data=io.BytesIO(result_json),
                length=len(result_json),
                content_type="application/json"
            )

            steps_list = [s.strip() for s in pipeline_steps.split(',') if s.strip()]
            if current_step < len(steps_list) - 1:
                next_step_index = current_step + 1
                next_worker = steps_list[next_step_index]
                cur.execute(
                    'UPDATE "Jobs" SET "CurrentStepIndex" = %s, "TargetWorker" = %s, "Status" = \'pending\' WHERE "Id" = %s',
                    (next_step_index, next_worker, job_id)
                )
                conn.commit()
                self.logger.info(f"Routing Slip: JobId {job_id} advanced to step {next_step_index} ({next_worker})")
            else:
                cur.execute('UPDATE "Jobs" SET "Status" = \'completed\' WHERE "Id" = %s', (job_id,))
                conn.commit()
                self.logger.info(f"JobId {job_id} fully completed.")
            status = "success"
        except Exception as e:
            self.logger.error(f"Failed to process JobId {job_id}: {e}")
            conn.rollback()
            try:
                cur.execute('UPDATE "Jobs" SET "Status" = \'failed\' WHERE "Id" = %s', (job_id,))
                conn.commit()
            except Exception as inner_e:
                self.logger.error(f"Critical fallback failure for JobId {job_id}: {inner_e}")
        finally:
            duration = time.time() - start_time
            JOBS_PROCESSED.labels(worker=worker_name, status=status).inc()
            JOB_DURATION.labels(worker=worker_name).observe(duration)
            JOBS_IN_PROGRESS.labels(worker=worker_name).dec()