import os
from prosd_worker import WorkerNode

# Set worker name for metrics and logs
os.environ.setdefault("WORKER_NAME", "worker-analyzer")

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
        "inputNumbers": {
            "type": "array",
            "items": {"type": "number"},
            "title": "Числа для аналізу"
        }
    },
    "required": ["inputNumbers"]
}

@app.algorithm(
    name="number-analyzer",
    category="testing",
    description="Аналізує числа і повертає масив з числових та буквених значень",
    input_schema=SCHEMA
)
def analyze_numbers(parameters):
    numbers = parameters.get("inputNumbers", [])
    mixed_result = []
    for num in numbers:
        try:
            val = float(num)
            mixed_result.append(val)
            if val > 0:
                mixed_result.append("Positive")
            elif val < 0:
                mixed_result.append("Negative")
            else:
                mixed_result.append("Zero")
        except (ValueError, TypeError):
            mixed_result.append(num)
            mixed_result.append("Not a Number")
    return {
        "analysis_result": mixed_result,
        "inputNumbers": [n for n in mixed_result if isinstance(n, (int, float))]
    }

if __name__ == "__main__":
    app.start()