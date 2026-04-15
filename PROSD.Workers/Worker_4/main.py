import os
import random
from prosd_worker import WorkerNode

# Set worker name for metrics and logs
os.environ.setdefault("WORKER_NAME", "worker-generator")

app = WorkerNode(
    gateway_meta_url=os.getenv("GATEWAY_META_URL", "http://localhost:8080/api/meta/register"),
    db_config={
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "prosd_db"),
        "user": os.getenv("DB_USER", "admin"),
        "password": os.getenv("DB_PASSWORD", "password123")
    },
    minio_config={
        "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        "secure": os.getenv("MINIO_SECURE", "False").lower() in ('true', '1', 't'),
        "bucket_name": os.getenv("MINIO_BUCKET_NAME", "pipeline-runs")
    }
)

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "n": {
            "type": "integer",
            "title": "Кількість елементів (n)",
            "minimum": 1,
            "default": 5
        },
        "min": {
            "type": "number",
            "title": "Мінімальне значення",
            "default": 0.0
        },
        "max": {
            "type": "number",
            "title": "Максимальне значення",
            "default": 10.0
        }
    },
    "required": ["n", "min", "max"]
}

@app.algorithm(
    name="float-generator",
    category="generation",
    description="Генерує масив випадкових дійсних чисел у заданому діапазоні",
    input_schema=SCHEMA
)
def generate_floats(parameters):
    n = int(parameters.get("n", 5))
    min_val = float(parameters.get("min", 0.0))
    max_val = float(parameters.get("max", 10.0))
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    generated_array = [round(random.uniform(min_val, max_val), 2) for _ in range(n)]
    return {
        "generated_count": n,
        "range": f"[{min_val}, {max_val}]",
        "inputNumbers": generated_array
    }

if __name__ == "__main__":
    app.start()