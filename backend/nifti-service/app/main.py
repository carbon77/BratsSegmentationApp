import struct
import tempfile
from pathlib import Path

import cv2
import nibabel as nib
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response

IMG_SIZE = 128
VOLUME_SLICES = 96
VOLUME_START_AT = 24
MODALITIES = ("t1", "t1ce", "t2", "flair")

TENSOR_MAGIC = 0x54454E53  # TENS
VOLUME_MAGIC = 0x564F4C31  # VOL1
SLICE_MAGIC = 0x534C4331  # SLC1

app = FastAPI(title="BraTS NIfTI preprocessing service")


def _load_nifti(path: Path) -> np.ndarray:
    return nib.load(path).get_fdata()


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    with destination.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            output.write(chunk)
    await upload.seek(0)


def _case_tensor(paths: dict[str, Path]) -> np.ndarray:
    volumes = [_load_nifti(paths[modality]) for modality in MODALITIES]
    tensor = np.zeros((1, len(MODALITIES), VOLUME_SLICES, IMG_SIZE, IMG_SIZE), dtype=np.float32)

    for z in range(VOLUME_SLICES):
        source_z = z + VOLUME_START_AT
        for channel, volume in enumerate(volumes):
            tensor[0, channel, z] = cv2.resize(volume[:, :, source_z], (IMG_SIZE, IMG_SIZE)).astype(np.float32)

    max_value = np.max(tensor)
    if max_value > 0:
        tensor /= max_value
    return tensor


def _mask_volume(path: Path) -> np.ndarray:
    mask = _load_nifti(path)
    volume = np.zeros((VOLUME_SLICES, IMG_SIZE, IMG_SIZE), dtype=np.uint8)
    for z in range(VOLUME_SLICES):
        volume[z] = cv2.resize(
            mask[:, :, z + VOLUME_START_AT],
            (IMG_SIZE, IMG_SIZE),
            interpolation=cv2.INTER_NEAREST,
        ).astype(np.uint8)
    return volume


def _modality_slice(path: Path, slice_idx: int) -> np.ndarray:
    image = _load_nifti(path)
    source_z = slice_idx + VOLUME_START_AT
    if slice_idx < 0 or source_z >= image.shape[2]:
        raise IndexError("Slice index out of range")
    return cv2.resize(image[:, :, source_z], (IMG_SIZE, IMG_SIZE)).astype(np.float32)


def _tensor_response(tensor: np.ndarray) -> Response:
    header = struct.pack(">6i", TENSOR_MAGIC, *tensor.shape)
    payload = tensor.astype(">f4", copy=False).tobytes(order="C")
    return Response(header + payload, media_type="application/octet-stream")


def _volume_response(volume: np.ndarray) -> Response:
    header = struct.pack(">4i", VOLUME_MAGIC, *volume.shape)
    return Response(header + volume.astype(np.uint8, copy=False).tobytes(order="C"), media_type="application/octet-stream")


def _slice_response(image_slice: np.ndarray) -> Response:
    header = struct.pack(">3i", SLICE_MAGIC, *image_slice.shape)
    payload = image_slice.astype(">f4", copy=False).tobytes(order="C")
    return Response(header + payload, media_type="application/octet-stream")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/preprocess/case")
async def preprocess_case(
    t1: UploadFile = File(...),
    t1ce: UploadFile = File(...),
    t2: UploadFile = File(...),
    flair: UploadFile = File(...),
) -> Response:
    uploads = {"t1": t1, "t1ce": t1ce, "t2": t2, "flair": flair}
    with tempfile.TemporaryDirectory(prefix="brats-nifti-") as tmp:
        tmp_dir = Path(tmp)
        paths: dict[str, Path] = {}
        for modality, upload in uploads.items():
            path = tmp_dir / f"{modality}.nii"
            await _save_upload(upload, path)
            paths[modality] = path
        return _tensor_response(_case_tensor(paths))


@app.post("/preprocess/mask")
async def preprocess_mask(true_mask: UploadFile = File(...)) -> Response:
    with tempfile.TemporaryDirectory(prefix="brats-mask-") as tmp:
        path = Path(tmp) / "true_mask.nii"
        await _save_upload(true_mask, path)
        return _volume_response(_mask_volume(path))


@app.post("/preprocess/slice")
async def preprocess_slice(
    modality: UploadFile = File(...),
    slice_idx: int = 1,
) -> Response:
    with tempfile.TemporaryDirectory(prefix="brats-slice-") as tmp:
        path = Path(tmp) / "modality.nii"
        await _save_upload(modality, path)
        return _slice_response(_modality_slice(path, slice_idx))
