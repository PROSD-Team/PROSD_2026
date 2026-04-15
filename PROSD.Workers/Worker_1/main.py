import os
from prosd_worker import WorkerNode

# Set worker name for metrics and logs
os.environ.setdefault("WORKER_NAME", "worker-math")

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
        "numbers": {
            "type": "array",
            "items": {"type": "number"},
            "title": "Масив чисел"
        },
        "multiplier": {
            "type": "number",
            "title": "Множник",
            "default": 2
        }
    },
    "required": ["numbers"]
}

@app.algorithm(
    name="math-multiplier",
    category="testing",
    description="Множить кожен елемент масиву на задане число",
    input_schema=SCHEMA
)
def multiply_array(parameters):
    numbers = parameters.get("numbers") or parameters.get("inputNumbers") or []
    multiplier = parameters.get("multiplier", 2)
    result_array = [float(x) * float(multiplier) for x in numbers]
    return {
        "original_count": len(numbers),
        "inputNumbers": result_array,
        "applied_multiplier": multiplier
    }

if __name__ == "__main__":
    app.start()