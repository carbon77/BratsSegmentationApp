# BraTS Segmentation Spring Boot Backend

This backend replaces the previous FastAPI/PyTorch service with a Java Spring Boot API that runs segmentation through ONNX Runtime.

## Build

```bash
mvn package
```

## Convert the PyTorch model to ONNX

Install the Python export dependencies in an environment with `torch`, `onnx`, and `onnxruntime`, then run:

```bash
python scripts/convert_model_to_onnx.py --checkpoint model.pth --output model.onnx
```

The Docker image expects `backend/model.onnx` to exist. At runtime, override the model location with `ONNX_MODEL_PATH` if needed.

## API

The API remains compatible with the frontend:

- `POST /predict`
- `GET /scans`
- `GET /scans/events`
- `GET /scans/{case_id}/result/metrics`
- `GET /scans/{case_id}/result/images?slice_idx=60&overlay_modality=t1`
- `PATCH /scans/{case_id}`
- `DELETE /scans/{case_id}`
