"""
Аспект логування -cross-cutting функціональність для всіх мікросервісів.
Реалізація AOP-подібного логування за допомогою декораторів Python.
"""
import functools
import logging
import time
import uuid
import json
from typing import Callable
import inspect

# Налаштування структурованого логера у форматі JSON 
def get_logger(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "service": "%(name)s", '
            '"level": "%(levelname)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_execution(service_name: str = "unknown", include_args: bool = False):
    """
    Декоратор логування AOP - записує вхід у функцію, вихід, тривалість виконання та помилки для будь-якої функції.
    Використання:
        @log_execution(service_name="text-processing")
        def my_endpoint_handler(...): ...
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(service_name)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())[:8]
            start_time = time.perf_counter()
            log_ctx = {
                "request_id": request_id,
                "function": func.__name__,
            }
            if include_args and kwargs:
                log_ctx["args"] = {k: str(v)[:100] for k, v in kwargs.items()}

            logger.info(json.dumps({"event": "ENTER", **log_ctx}))
            try:
                result = await func(*args, **kwargs)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.info(json.dumps({
                    "event": "EXIT",
                    "duration_ms": duration_ms,
                    **log_ctx
                }))
                return result
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(json.dumps({
                    "event": "ERROR",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "duration_ms": duration_ms,
                    **log_ctx
                }))
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Аналогічна логіка для синхронних функцій
            request_id = str(uuid.uuid4())[:8]
            start_time = time.perf_counter()
            log_ctx = {"request_id": request_id, "function": func.__name__}
            logger.info(json.dumps({"event": "ENTER", **log_ctx}))
            try:
                result = func(*args, **kwargs)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.info(json.dumps({"event": "EXIT", "duration_ms": duration_ms, **log_ctx}))
                return result
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(json.dumps({
                    "event": "ERROR", "error": str(exc), 
                    "error_type": type(exc).__name__, "duration_ms": duration_ms, **log_ctx
                }))
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator