# Brain Tumor Segmentation App

Веб-приложение для загрузки МРТ-исследований в формате NIfTI, запуска сегментации опухоли головного мозга и просмотра результатов в браузере.

## Возможности

- Регистрация, вход и хранение JWT на клиенте.
- Приватный список сканов для каждого пользователя.
- Загрузка обязательных модальностей `t1`, `t1ce`, `t2`, `flair` и опциональной истинной маски `true_mask`.
- Автоматическое сопоставление модальностей по имени файла.
- Асинхронная обработка через Kafka и отдельный worker-процесс.
- Просмотр метрик качества сегментации.
- Просмотр PNG-среза маски и наложение маски на выбранную МРТ-модальность.
- Переименование и удаление сканов.
- Переключение языка интерфейса: русский / английский.
- Переключение темы интерфейса: светлая / тёмная / системная.

## Архитектура

Приложение разделено на frontend, API backend, очередь задач, worker сегментации, PostgreSQL и S3-совместимое объектное хранилище.

```mermaid
flowchart LR
    User[Пользователь] --> Browser[Vue SPA]
    Browser -->|HTTP /api + SSE| Nginx[Nginx reverse proxy]
    Nginx --> Frontend[Vite frontend]
    Nginx --> Backend[FastAPI backend]

    Backend -->|JWT auth, scans metadata| Postgres[(PostgreSQL)]
    Backend -->|stage upload task| Kafka[(Kafka topic)]
    Backend -->|temporary upload staging| Staging[(upload_staging volume)]

    Kafka --> Worker[Segmentation worker]
    Worker -->|read staged files| Staging
    Worker -->|upload modalities/results| ObjectStorage[(S3-compatible storage)]
    Worker -->|update status, metrics, result_path| Postgres

    Backend -->|download result files / render slices| ObjectStorage
    Backend -->|metrics and generated PNG slices| Browser
```

### Frontend

Frontend находится в каталоге `frontend/` и реализован на Vue 3 + Vite + PrimeVue.

- `frontend/src/App.vue` — общий каркас приложения: верхняя панель, кнопки языка, кнопки темы, состояние пользователя.
- `frontend/src/pages/HomePage.vue` — главная страница с панелью загрузки и списком сканов.
- `frontend/src/components/home/UploadPanel.vue` — выбор NIfTI-файлов и автоматическое сопоставление модальностей.
- `frontend/src/components/home/ScansList.vue` — поиск, сортировка, открытие и удаление сканов.
- `frontend/src/pages/ScanPage.vue` — страница конкретного скана с метриками, редактированием названия и просмотром срезов.
- `frontend/src/components/scan/MetricsTable.vue` — группированная таблица метрик.
- `frontend/src/components/scan/SliceViewer.vue` — загрузка, просмотр и скачивание PNG-срезов.
- `frontend/src/services/api.js` — Axios-клиент, JWT, REST-запросы и SSE-подписка на обновления сканов.
- `frontend/src/services/preferences.js` — локальные настройки языка и темы.

### Backend API

Backend находится в каталоге `backend/` и реализован на FastAPI.

- `backend/app/main.py` — создание приложения, подключение роутера, инициализация схемы БД и Kafka producer в lifespan.
- `backend/app/api/routes.py` — HTTP API: auth, upload, scans, metrics, images, SSE, delete, patch.
- `backend/app/db/models.py` — SQLAlchemy-модели пользователей и сканов.
- `backend/app/services/auth.py` — JWT, хеширование паролей и получение текущего пользователя.
- `backend/app/services/storage.py` — staging файлов, работа с S3-compatible storage и удаление артефактов.
- `backend/app/services/tasks.py` — producer задач сегментации в Kafka.
- `backend/app/services/results.py` — отрисовка PNG-срезов через matplotlib.
- `backend/app/services/preprocessing.py` — подготовка выбранного среза модальности для наложения.
- `backend/app/services/segmentation.py` и `backend/app/services/inference.py` — запуск модели и расчёт результатов.

### Worker

`backend/app/worker.py` запускается отдельным контейнером `segmentation-worker`.

1. Читает задачу из Kafka topic `segmentation-tasks`.
2. Загружает staged-файлы в S3-compatible storage.
3. Переводит скан в статус `processing`.
4. Запускает сегментацию.
5. Сохраняет путь к результату и метрики в PostgreSQL.
6. Переводит скан в статус `completed` или `failed`.
7. Удаляет временные staged-файлы.

## Поток обработки скана

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant F as Vue frontend
    participant A as FastAPI backend
    participant K as Kafka
    participant W as Worker
    participant DB as PostgreSQL
    participant S3 as S3-compatible storage

    U->>F: Выбирает t1/t1ce/t2/flair
    F->>A: POST /predict multipart/form-data
    A->>DB: Создать Scan(status=uploading)
    A->>K: enqueue segmentation task
    A-->>F: 202 + case_id/status
    F->>A: GET /scans/events
    K->>W: segmentation task
    W->>S3: Загрузить исходные файлы
    W->>DB: status=processing
    W->>W: Запустить модель сегментации
    W->>S3: Сохранить результат
    W->>DB: status=completed, metrics, result_path
    A-->>F: SSE: обновлённый список сканов
    F->>A: GET metrics/images
    A-->>F: Метрики и PNG-срезы
```

## Стек

### Frontend

- Vue 3
- Vite
- PrimeVue
- PrimeIcons
- Axios

### Backend и ML

- FastAPI
- SQLAlchemy
- PostgreSQL
- Kafka / aiokafka
- PyTorch
- PyTorch Lightning
- nibabel
- numpy
- matplotlib
- pandas
- S3-compatible object storage, например Yandex Cloud Object Storage

### Инфраструктура

- Docker Compose
- Nginx reverse proxy
- Отдельные контейнеры для frontend, backend, worker, PostgreSQL и Kafka

## Как запустить

### 1. Подготовить переменные окружения backend

Создайте файл `backend/.env`. Минимальный пример для локального запуска через Docker Compose:

```env
JWT_SECRET_KEY=change-me-in-local-dev
ACCESS_TOKEN_EXPIRE_MINUTES=1440

AWS_S3_BUCKET=brats
AWS_REGION=ru-central1
AWS_S3_ENDPOINT_URL=https://storage.yandexcloud.net
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

LOG_LEVEL=INFO
```

`DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS` и `UPLOAD_STAGING_DIR` уже задаются в `docker-compose.yml` для контейнеров.

### 2. Запустить весь стек

```bash
docker compose up --build
```

После запуска доступны:

- Web UI через Nginx: <http://localhost/>
- Backend API напрямую: <http://localhost:8000/>
- Frontend preview контейнер напрямую: <http://localhost:4173/>
- Orthanc Web UI: <http://localhost:8042/> (логин/пароль: `orthanc` / `orthanc`)

### 3. Открыть приложение

1. Перейдите на <http://localhost/>.
2. Зарегистрируйте пользователя.
3. Загрузите 4 NIfTI-файла с модальностями `t1`, `t1ce`, `t2`, `flair`.
4. Дождитесь статуса `Completed` / `Готово` в списке сканов.
5. Откройте скан, посмотрите метрики и загрузите нужный срез.

## Локальная разработка без полного Docker Compose

### Backend

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

Для полноценной обработки сканов backend должен видеть PostgreSQL, Kafka и S3-compatible storage. Если они запущены через Docker Compose, укажите локальные значения переменных окружения, например:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/brats
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
UPLOAD_STAGING_DIR=./upload-staging
```

Worker можно запустить отдельно:

```bash
cd backend
uv run python -m app.worker
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Vite dev server поднимется на локальном порту, который будет показан в терминале. Для API-запросов frontend ожидает префикс `/api`; в production его проксирует Nginx.

## API

Все защищённые endpoints требуют заголовок `Authorization: Bearer <JWT>`.

| Метод | Endpoint | Описание |
| --- | --- | --- |
| `POST` | `/auth/register` | Создаёт пользователя и возвращает JWT. |
| `POST` | `/auth/login` | Аутентифицирует пользователя и возвращает JWT. |
| `GET` | `/auth/me` | Возвращает текущего пользователя. |
| `POST` | `/predict` | Загружает MRI-модальности и ставит задачу сегментации в очередь. |
| `GET` | `/scans` | Возвращает список сканов текущего пользователя. |
| `GET` | `/scans/events` | SSE-поток обновлений списка сканов. |
| `GET` | `/scans/{case_id}/result/metrics` | Возвращает сохранённые метрики сегментации. |
| `GET` | `/scans/{case_id}/result/images?slice_idx=60&overlay_modality=t1` | Возвращает PNG-срез маски, опционально с наложением на модальность. |
| `PATCH` | `/scans/{case_id}` | Обновляет метаданные скана, сейчас — название. |
| `DELETE` | `/scans/{case_id}` | Удаляет скан и связанные файлы. |

## Основные переменные окружения

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/brats` | Строка подключения SQLAlchemy к PostgreSQL. |
| `JWT_SECRET_KEY` | `change-me-in-production` | Секрет для подписи JWT; в production обязательно замените. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Время жизни access token. |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Адрес Kafka broker. |
| `SEGMENTATION_TOPIC` | `segmentation-tasks` | Topic для задач сегментации. |
| `SEGMENTATION_CONSUMER_GROUP` | `segmentation-workers` | Consumer group worker-процессов. |
| `UPLOAD_STAGING_DIR` | зависит от сервиса | Каталог временного staging перед загрузкой в S3. |
| `AWS_S3_BUCKET` | `brats` | Bucket для исходных файлов и результатов. |
| `AWS_REGION` | `ru-central1` | Регион S3-compatible storage. |
| `AWS_S3_ENDPOINT_URL` | `https://storage.yandexcloud.net` | Endpoint объектного хранилища. |
| `AWS_ACCESS_KEY_ID` | пусто | Access key для S3. |
| `AWS_SECRET_ACCESS_KEY` | пусто | Secret key для S3. |
| `LOG_LEVEL` | `INFO` | Уровень логирования worker. |

## Формат загружаемых файлов

- Поддерживаются `.nii` и `.nii.gz`.
- Обязательные модальности: `t1`, `t1ce`, `t2`, `flair`.
- При массовом выборе frontend ищет ключевые слова в имени файла.
- Для `t1ce` проверка выполняется раньше `t1`, чтобы файл `t1ce` не был ошибочно отнесён к `t1`.
- `true_mask` можно загрузить дополнительно, если нужно сравнение с истинной маской.

## Полезные команды

```bash
# Запуск всего стека
docker compose up --build

# Остановка контейнеров
docker compose down

# Остановка с удалением volume данных
docker compose down -v

# Сборка frontend
cd frontend && pnpm build

# Запуск backend worker локально
cd backend && uv run python -m app.worker
```

## Troubleshooting

- Если сканы остаются в статусе `Uploading`, проверьте Kafka и логи `segmentation-worker`.
- Если статус `Failed`, проверьте доступность S3-compatible storage, корректность credentials и формат NIfTI-файлов.
- Если список сканов не обновляется автоматически, проверьте endpoint `/api/scans/events` и Nginx buffering; конфигурация должна отключать буферизацию SSE.
- Если PNG-срез не строится, убедитесь, что скан в статусе `completed`, а `slice_idx` находится внутри размеров загруженного объёма.

## Экспорт метрик в Orthanc

На странице скана доступны действия:

- `Export JSON` / `Экспорт JSON` — локальная выгрузка метрик.
- `Export CSV` / `Экспорт CSV` — локальная выгрузка метрик.
- `Upload to Orthanc` / `Выгрузить в Orthanc` — отправляет оба файла (JSON и CSV) в Orthanc через backend как DICOM-инстансы с инкапсулированным содержимым.

Backend использует переменные окружения:

- `ORTHANC_URL` (по умолчанию `http://orthanc:8042`)
- `ORTHANC_USERNAME` (по умолчанию `orthanc`)
- `ORTHANC_PASSWORD` (по умолчанию `orthanc`)
