"""
Модуль для роботи зі сховищем.
Підтримує MinIO (S3-сумісне сховище) та локальну файлову систему як резерв.
"""
import os
import json
import yaml
from pathlib import Path
from datetime import datetime
import boto3

#перевіряємо, чи налаштований MinIO - змінні середовища
USE_MINIO = os.getenv("USE_MINIO", "false").lower() == "true"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "linglab-outputs")
WORKING_FOLDER = os.getenv("WORKING_FOLDER", "/tmp/linglab_outputs")

def save_job_output(category: str, algorithm: str, job_id: str, parameters: dict, results: dict, large_files: dict[str, bytes] | None = None) -> tuple[str, dict]:
    """
    Зберігає результати роботи алгоритму (конфігурацію, метрики та великі файли).
    Повертає шлях до папки (або префікс у бакеті) та оновлений словник результатів.
    """
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    folder_name = f"{category}_{algorithm}_{ts}_{job_id[:8]}"
    
    output_results = dict(results)
    
    # Якщо використовуємо MinIO, ці налаштування не первірені бо не користувався MinIO, але мають працювати 
    # TODO: протестувати з MinIO
    if USE_MINIO:
        s3 = boto3.client( 's3', endpoint_url=MINIO_ENDPOINT, aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"), aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin") )
        
        # Завантажує config.yaml
        config_data = yaml.dump({"parameters": parameters}, allow_unicode=True)
        s3.put_object(Bucket=MINIO_BUCKET, Key=f"{folder_name}/config.yaml", Body=config_data.encode('utf-8'))
        
        # Завантажує великі файли
        if large_files:
            for filename, content in large_files.items():
                s3.put_object(Bucket=MINIO_BUCKET, Key=f"{folder_name}/{filename}", Body=content)
                key = Path(filename).stem.replace("-", "_")
                output_results[key] = f"s3://{MINIO_BUCKET}/{folder_name}/{filename}"
        
        # Завантажує output.json
        s3.put_object(Bucket=MINIO_BUCKET, Key=f"{folder_name}/output.json", Body=json.dumps(output_results, ensure_ascii=False).encode('utf-8'))
        
        return f"s3://{MINIO_BUCKET}/{folder_name}", output_results

    #якщо використовуємо локальну файлову систему (наприклад, для розробки і поки забити на MinIO)
    folder_path = Path(WORKING_FOLDER) / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    with open(folder_path / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"parameters": parameters}, f, allow_unicode=True)

    if large_files:
        for filename, content in large_files.items():
            file_dest = folder_path / filename
            file_dest.write_bytes(content if isinstance(content, bytes) else content.encode())
            key = Path(filename).stem.replace("-", "_")
            output_results[key] = filename

    with open(folder_path / "output.json", "w", encoding="utf-8") as f:
        json.dump(output_results, f, ensure_ascii=False, indent=2)

    return str(folder_path), output_results