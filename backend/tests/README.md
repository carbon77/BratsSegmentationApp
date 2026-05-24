# Backend

## Запуск тестов

Тесты находятся в каталоге `backend/tests` и запускаются из папки `backend`.

### 1) Установить зависимости

Рекомендуемый способ — через `uv`:

```bash
cd backend
uv sync
```

Альтернатива через `pip`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Запустить все тесты

```bash
cd backend
uv run pytest -q
```

### 3) Запустить отдельные группы тестов

Unit-тесты:

```bash
cd backend
uv run pytest -q tests/test_unit_auth_and_dto.py
```

Интеграционные тесты:

```bash
cd backend
uv run pytest -q tests/test_integration_auth_routes.py
```

Нагрузочный (load-style) тест:

```bash
cd backend
uv run pytest -q tests/test_load_scans.py
```

### Полезно при ошибке `ModuleNotFoundError: app`

Если тесты запускаются не через `uv run`, укажите `PYTHONPATH`:

```bash
cd backend
PYTHONPATH=. pytest -q
```
