"""
Спільні моделі даних для всіх мікросервісів LingLab.
Визначають структуру повідомлень для RabbitMQ.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class JobMessage(BaseModel):
    """Модель повідомлення, яке API Gateway кладе в чергу RabbitMQ."""
    job_id: str = Field(..., description="Унікальний ідентифікатор задачі (UUID)")
    category: str = Field(..., description="Категорія алгоритму (наприклад, 'text-processing')")
    algorithm: str = Field(..., description="Назва алгоритму (наприклад, 'preprocessing')")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Вхідні параметри для алгоритму")
    
class JobResult(BaseModel):
    """Модель результату, який генерує Python-воркер після виконання задачі."""
    job_id: str
    status: str = Field(..., description="Статус: 'success' або 'error'")
    results: dict[str, Any] = Field(default_factory=dict, description="Короткі результати (без великих файлів)")
    duration_ms: float = Field(0.0, description="Тривалість виконання у мілісекундах")
    output_folder: Optional[str] = Field(None, description="Шлях до папки в MinIO/FileSystem")
    error_message: Optional[str] = Field(None, description="Повідомлення про помилку (якщо status == 'error')")