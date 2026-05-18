# BraTS Segmentation Spring Boot Backend

The backend is now split by responsibility:

- Java Spring Boot owns the public API, PostgreSQL persistence, Kafka task flow, S3 storage, ONNX Runtime inference, metrics, and PNG result rendering.
- A small Python NIfTI service owns NIfTI-specific loading and preprocessing with `nibabel`, `numpy`, and OpenCV.

## Build Java backend

```bash
mvn package
```

## Run the Python NIfTI service locally

```bash
cd nifti-service
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
```

Set `NIFTI_SERVICE_URL` for the Java backend if the service is not available at `http://localhost:8010`.

## Convert the PyTorch model to ONNX

Install the Python export dependencies in an environment with `torch`, `onnx`, and `onnxruntime`, then run:

```bash
python scripts/convert_model_to_onnx.py --checkpoint model.pth --output model.onnx
```

The Java service expects an ONNX model at `ONNX_MODEL_PATH` and runs inference through ONNX Runtime for Java.

## API

The API remains compatible with the frontend:

- `POST /predict`
- `GET /scans`
- `GET /scans/events`
- `GET /scans/{case_id}/result/metrics`
- `GET /scans/{case_id}/result/images?slice_idx=60&overlay_modality=t1`
- `PATCH /scans/{case_id}`
- `DELETE /scans/{case_id}`
