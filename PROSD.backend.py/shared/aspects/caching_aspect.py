"""
Аспект кешування- cross-cutting функціональність.

Реалізація AOP-подібного In-Memory кешування за допомогою декораторів Python.

Не було використано Redis або інші зовнішні кеші для простоти та автономності 
хоча можна легко адаптувати під будь-який бекенд тому що в архітектура не 
використовує інфраструктуру Redis
"""
import functools
import hashlib
import json
import time
from typing import Callable, Any, Optional
from collections import OrderedDict

class LRUCache:
    def __init__(self, maxsize: int = 256, ttl: int = 300):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        value, ts = self._cache[key]
        if time.time() - ts > self.ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.time())
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def clear(self):
        self._cache.clear()

_local_cache = LRUCache()

def _build_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    payload = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"

def cache_result(prefix: str, ttl: int = 300):
    """
    Декоратор кешування In-Memory.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                cache_key = _build_cache_key(prefix, args[1:], kwargs)
            except Exception:
                return await func(*args, **kwargs)

            # Спроба отримати значення з локального кешу в пам'яті
            cached = _local_cache.get(cache_key)
            if cached is not None:
                return cached

            # Виконання реальної функції
            result = await func(*args, **kwargs)

            # Збереження результату в локальному кеші
            try:
                _local_cache.set(cache_key, result)
            except Exception:
                pass

            return result
        return async_wrapper
    return decorator