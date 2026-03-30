# Brain Tumor Segmentation App

## Description

App where user can upload nifti files of mri scans and make segmentation masks

## Backend

- MRI modalities are uploaded to S3-compatible storage (Yandex Cloud Object Storage).
- Scan metadata and inference results are persisted via the `Scan` model in PostgreSQL.

## Stack

- Prediction model:
  - PyTorch
  - PyTorch Lightning: for training pipeline
  - nibabel: for `nifti` files
  - numpy, matplotlib, pandas
- Backend:
  - FastAPI
  - PostgreSQL
  - S3

## API

- `POST /predict` – uploads MRI modalities, runs inference, persists results.
- `GET /scans` – returns all scans case ids
- `GET /scans/{case_id}/result/metrics` – returns persisted segmentation metrics.
- `GET /scans/{case_id}/result/images?slice_idx=60` – returns prediction mask slice plot using `matplotlib`
- `DELETE /scans/{case_id}` – delete scan metadata and files

## Environment variables

- `DATABASE_URL` (optional, defaults to `postgresql+psycopg://postgres:postgres@localhost:5432/brats`)
- `AWS_S3_BUCKET` (optional, defaults to `brats`)
- `AWS_REGION` (optional, defaults to `ru-central1`)
- `AWS_S3_ENDPOINT_URL` (optional, defaults to `https://storage.yandexcloud.net`)
