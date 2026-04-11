# PROSD_2026 — Створення Python-воркера
> Покрокова інструкція розробника

---

## Крок 1 — Структура проєкту та залежності

Кожен воркер складається з двох основних файлів:

- **`prosd_worker.py`** — ядро системи, яке надається командою. Не редагувати. Копіювати з інших воркерів.
- **`main.py`** — ваш файл: бізнес-логіка та реєстрація алгоритмів.

**`requirements.txt`**

```
requests          # Реєстрація метаданих на Gateway
psycopg2-binary   # Доступ до PostgreSQL
minio             # Доступ до файлового сховища
pyyaml            # Читання конфігурацій
```

---

## Крок 2 — Ініціалізація WorkerNode

На початку файлу `main.py` імпортуйте та ініціалізуйте екземпляр класу `WorkerNode`. Вся конфігурація передається через змінні середовища, що робить мікросервіс готовим до розгортання у Docker / Kubernetes.

```python
# main.py
import os
from prosd_worker import WorkerNode

app = WorkerNode(
    gateway_meta_url=os.getenv(
        'GATEWAY_META_URL',
        'http://localhost:8080/api/meta/register'
    ),
    db_config={
        'host':     os.getenv('DB_HOST',     'localhost'),
        'port':     os.getenv('DB_PORT',     '5432'),
        'dbname':   os.getenv('DB_NAME',     'prosd_db'),
        'user':     os.getenv('DB_USER',     'admin'),
        'password': os.getenv('DB_PASSWORD', 'password123'),
    },
    minio_config={
        'endpoint':    os.getenv('MINIO_ENDPOINT',   'localhost:9000'),
        'access_key':  os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        'secret_key':  os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
        'secure':      os.getenv('MINIO_SECURE', 'False').lower()
                       in ('true', '1', 't'),
        'bucket_name': os.getenv('MINIO_BUCKET_NAME', 'pipeline-runs'),
    }
)
```

### Змінні середовища

| Змінна | Призначення |
|---|---|
| `GATEWAY_META_URL` | URL для реєстрації метаданих на .NET Gateway |
| `DB_HOST` / `DB_PORT` | Адреса та порт PostgreSQL |
| `DB_NAME` / `DB_USER` | Назва БД та ім'я користувача |
| `DB_PASSWORD` | Пароль до бази даних |
| `MINIO_ENDPOINT` | Адреса MinIO сховища |
| `MINIO_ACCESS_KEY` | Ключ доступу MinIO |
| `MINIO_SECRET_KEY` | Секретний ключ MinIO |
| `MINIO_BUCKET_NAME` | Назва бакету для зберігання результатів |

---

## Крок 3 — Створення JSON-схеми

Кожен алгоритм повинен мати власну JSON Schema. Вона виконує дві функції:

- **Автоматична генерація форми вводу** на фронтенді.
- **Валідація вхідних даних** перед виконанням алгоритму.

```python
SCHEMA = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'type': 'object',
    'properties': {
        'numbers': {
            'type': 'array',
            'items': {'type': 'number'},
            'title': 'Масив чисел'
        },
        'multiplier': {
            'type': 'number',
            'title': 'Множник',
            'default': 2
        }
    },
    'required': ['numbers']
}
```

> **Поля `required`**
> Усі поля, перелічені у масиві `required`, є обов'язковими. Їх відсутність у вхідних даних призведе до помилки валідації.

---

## Крок 4 — Реєстрація алгоритму (декоратор)

Для реєстрації функції-обробника як алгоритму використовуйте декоратор `@app.algorithm()`.

### Параметри декоратора

| Параметр | Опис |
|---|---|
| `name` | Унікальна назва алгоритму (використовується у `PipelineSteps`) |
| `category` | Категорія для групування на фронтенді: `testing`, `ml`, `data-processing` тощо |
| `description` | Короткий опис того, що робить алгоритм |
| `input_schema` | JSON Schema, визначена на попередньому кроці |

### Правила функції-обробника

- Приймає єдиний аргумент — словник `parameters`.
- Якщо воркер є **першим у конвеєрі**: `parameters` = дані з `config.yaml` (введені користувачем).
- Якщо воркер є **наступним кроком**: `parameters` = вміст `output.json` попереднього воркера.
- Повинна повертати **`dict`**, який система збереже як `output.json` для наступних кроків.

```python
@app.algorithm(
    name='math-multiplier',
    category='testing',
    description='Множить кожен елемент масиву на задане число',
    input_schema=SCHEMA
)
def multiply_array(parameters):
    # 1. Читаємо вхідні параметри
    #    Захист: дані можуть прийти від користувача ('numbers')
    #    або від попереднього воркера ('inputNumbers')
    numbers    = parameters.get('numbers') or parameters.get('inputNumbers') or []
    multiplier = parameters.get('multiplier', 2)

    # 2. Виконуємо обчислення
    result = [float(x) * float(multiplier) for x in numbers]

    # 3. Повертаємо словник — він стане output.json для наступного кроку
    return {
        'original_count':     len(numbers),
        'inputNumbers':       result,       # ключ для наступного воркера
        'applied_multiplier': multiplier
    }
```

> **Передача даних між воркерами**
> Якщо наступний воркер очікує ключ `'inputNumbers'`, поверніть результат саме під цим ключем. Узгодьте контракт між воркерами заздалегідь.

---

## Крок 5 — Запуск воркера

В кінці файлу `main.py` додайте виклик методу `app.start()`, який запускає нескінченний цикл опитування бази даних (Polling).

```python
if __name__ == '__main__':
    app.start()
```

### Повна структура `main.py`

```python
import os
from prosd_worker import WorkerNode

# ── 1. Ініціалізація ──────────────────────────────────
app = WorkerNode(
    gateway_meta_url=os.getenv('GATEWAY_META_URL', 'http://localhost:8080/api/meta/register'),
    db_config={ ... },
    minio_config={ ... }
)

# ── 2. JSON Schema ────────────────────────────────────
SCHEMA = { ... }

# ── 3. Алгоритм ──────────────────────────────────────
@app.algorithm(name='my-algorithm', category='testing',
               description='...', input_schema=SCHEMA)
def my_algorithm(parameters):
    ...
    return { ... }

# ── 4. Запуск ────────────────────────────────────────
if __name__ == '__main__':
    app.start()
```

---

## Як система працює «під капотом»

### Самореєстрація

При виклику `app.start()` воркер автоматично надсилає свої метадані (назву, категорію, JSON-схему) на .NET Gateway за адресою `GATEWAY_META_URL`. Після цього алгоритм стає доступним у фронтенді.

### Polling бази даних

Воркер постійно виконує запит `SELECT ... FOR UPDATE SKIP LOCKED` до PostgreSQL. Це блокування на рівні рядка гарантує:

- Кілька копій одного воркера ніколи не візьмуть одне завдання одночасно.
- Горизонтальне масштабування без додаткової координації.

### Робота зі сховищем MinIO

- **Перший крок пайплайну:** читає вхідні дані з `config.yaml`.
- **Кожен наступний крок:** читає `output.json` попереднього воркера з папки `S3FolderPath`.
- **Після виконання:** результат зберігається як `output.json` у тій самій папці.

### Routing Slip (Естафета)

Після того як функція повернула результат, ядро виконує такі дії:

1. Перевіряє масив `PipelineSteps` — чи є наступний крок.
2. Якщо так: статус завдання → `pending`, поле `TargetWorker` → назва наступного мікросервісу.
3. Якщо кроків більше немає: статус → `completed`.

---

## Чек-лист перед деплоєм

- [ ] `prosd_worker.py` знаходиться у тій самій директорії, що й `main.py`.
- [ ] Всі змінні середовища визначені у `docker-compose` або Kubernetes manifest.
- [ ] Назва алгоритму (`name`) унікальна в межах системи.
- [ ] JSON Schema містить усі обов'язкові поля у `required`.
- [ ] Функція-обробник повертає `dict`, а не `None` чи список.
- [ ] Ключі вихідного словника узгоджені з наступним воркером у пайплайні.
- [ ] `app.start()` викликається в блоці `if __name__ == '__main__':`.

# PROSD_2026 - Створення .Net-воркера самі напишете я не робив 