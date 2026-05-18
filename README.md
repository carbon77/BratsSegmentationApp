# Brain Tumor Segmentation App

## Description

App where users upload BraTS MRI NIfTI modalities and receive segmentation masks, slice previews, and optional overlap metrics.

## Stack

- Frontend: Vue + Vite
- Backend API/orchestration: Java 21, Spring Boot, Spring MVC, Spring Data JPA, Spring Kafka, Lombok
- NIfTI preprocessing: Python service with FastAPI, nibabel, numpy, and OpenCV
- Inference: ONNX Runtime for Java
- Persistence: PostgreSQL
- Object storage: S3-compatible storage such as Yandex Cloud Object Storage
- Messaging: Kafka segmentation task queue

## Model conversion

The Java backend uses an ONNX model. Convert the existing PyTorch checkpoint before running inference:

```bash
cd backend
python scripts/convert_model_to_onnx.py --checkpoint model.pth --output model.onnx
```

The converter exports a `[1, 4, 96, 128, 128]` input tensor model and verifies it with ONNX Runtime by default. Set `ONNX_MODEL_PATH` if the model is stored somewhere other than `/app/model.onnx`.

## NIfTI service

NIfTI file loading, resizing, normalization, true-mask preprocessing, and overlay-slice extraction remain in Python. The Java backend calls the service through `NIFTI_SERVICE_URL` and then performs ONNX inference and persistence itself.

```bash
cd backend/nifti-service
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## Backend API

- `POST /predict` - uploads MRI modalities, queues segmentation, persists scan metadata.
- `GET /scans` - returns all scan case ids, titles, and statuses.
- `GET /scans/events` - streams scan list updates with server-sent events.
- `GET /scans/{case_id}/result/metrics` - returns persisted segmentation metrics.
- `GET /scans/{case_id}/result/images?slice_idx=60&overlay_modality=t1` - returns a PNG mask slice, optionally overlaid on an MRI modality.
- `DELETE /scans/{case_id}` - deletes scan metadata and files.
- `PATCH /scans/{case_id}` - patches scan metadata.

## Environment variables

- `DATABASE_URL` (optional, defaults to `jdbc:postgresql://localhost:5432/brats`)
- `DATABASE_USERNAME` (optional, defaults to `postgres`)
- `DATABASE_PASSWORD` (optional, defaults to `postgres`)
- `KAFKA_BOOTSTRAP_SERVERS` (optional, defaults to `localhost:9092`)
- `SEGMENTATION_TOPIC` (optional, defaults to `segmentation-tasks`)
- `ONNX_MODEL_PATH` (optional, defaults to `/app/model.onnx`)
- `NIFTI_SERVICE_URL` (optional, defaults to `http://localhost:8010`)
- `AWS_S3_BUCKET` (optional, defaults to `brats`)
- `AWS_REGION` (optional, defaults to `ru-central1`)
- `AWS_S3_ENDPOINT_URL` (optional, defaults to `https://storage.yandexcloud.net`)
- `AWS_S3_ACCESS_KEY` / `AWS_ACCESS_KEY_ID`
- `AWS_S3_SECRET_KEY` / `AWS_SECRET_ACCESS_KEY`
