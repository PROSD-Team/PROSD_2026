import re
from shared.aspects import log_execution, cache_result, ValidationError

# Кешуємо результати на 5 хвилин (300 сек) у локальній пам'яті
@cache_result(prefix="algo:preprocess", ttl=300)
@log_execution(service_name="text-processing", include_args=False)
async def preprocess_text(text: str, lowercase: bool = True, remove_punctuation: bool = True) -> dict:
    """Очищує текст та рахує статистику."""
    if not text or not text.strip():
        raise ValidationError("Параметр 'text' є обов'язковим і не може бути порожнім.")

    result = text
    if lowercase:
        result = result.lower()
    if remove_punctuation:
        result = re.sub(r"[^\w\s]", "", result)
    
    result = re.sub(r"\s+", " ", result).strip()
    words = result.split()
    
    return {
        "word_count": len(words),
        "char_count": len(result),
        "unique_words": len(set(words)),
        "processed_text": result
    }