import os
from prosd_worker import WorkerNode

# Set worker name for metrics and logs
os.environ.setdefault("WORKER_NAME", "worker-profiler")

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
        "username": {"type": "string", "title": "Ім'я користувача", "default": "System"},
        "age": {"type": "integer", "title": "Вік", "default": 0},
        "score": {"type": "number", "title": "Бал", "default": 0.0},
        "isActive": {"type": "boolean", "title": "Активний статус", "default": True}
    },
    "required": ["username"]
}

@app.algorithm(
    name="data-profiler",
    category="testing",
    description="Збирає різні змінні в один змішаний масив",
    input_schema=SCHEMA
)
def generate_profile(parameters):
    username = parameters.get("username", "Unknown")
    age = parameters.get("age", 0)
    score = parameters.get("score", 0.0)
    is_active = parameters.get("isActive", False)
    previous_results = parameters.get("analysis_result", [])
    mixed_array = [
        "PROFILE_START",
        "USER:", username,
        "AGE:", age,
        "SCORE:", score,
        "STATUS:", "Active" if is_active else "Inactive"
    ]
    if previous_results:
        mixed_array.append("PREVIOUS_STEPS_DATA:")
        mixed_array.extend(previous_results)
    mixed_array.append("PROFILE_END")
    return {
        "profile_array": mixed_array,
        "final_summary": f"User {username} processed with {len(previous_results)} data points"
    }

if __name__ == "__main__":
    app.start()