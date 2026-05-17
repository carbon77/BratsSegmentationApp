import asyncio
import io
import os
import shutil
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import boto3
import numpy as np

from app.db.models import Scan

S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'brats')
AWS_REGION = os.getenv('AWS_REGION', 'ru-central1')
AWS_S3_ACCESS_KEY = os.getenv('AWS_S3_ACCESS_KEY')
AWS_S3_SECRET_KEY = os.getenv('AWS_S3_SECRET_KEY')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'https://storage.yandexcloud.net')
UPLOAD_STAGING_DIR = os.getenv('UPLOAD_STAGING_DIR', '/tmp/brats-upload-staging')

_s3 = boto3.client(
    's3',
    region_name=AWS_REGION,
    endpoint_url=AWS_S3_ENDPOINT_URL,
    aws_access_key_id=AWS_S3_ACCESS_KEY,
    aws_secret_access_key=AWS_S3_SECRET_KEY,
)


def _to_s3_uri(key: str) -> str:
    return f's3://{S3_BUCKET}/{key}'


def _from_s3_uri(uri: str) -> str:
    expected_prefix = f's3://{S3_BUCKET}/'
    if not uri.startswith(expected_prefix):
        raise ValueError(f'Invalid S3 URI: {uri}')
    return uri.removeprefix(expected_prefix)


def _case_staging_dir(case_id: str) -> str:
    return os.path.join(UPLOAD_STAGING_DIR, case_id)


def _copy_upload_to_path(upload_file, path: str) -> None:
    with open(path, 'wb') as output:
        shutil.copyfileobj(upload_file, output)


async def _stage_single(name: str, upload_file, case_dir: str) -> tuple[str, str]:
    local_path = os.path.join(case_dir, f'{name}.nii')
    await upload_file.seek(0)
    await asyncio.to_thread(_copy_upload_to_path, upload_file.file, local_path)
    return name, local_path


async def stage_uploaded_files(files) -> tuple[str, str, dict[str, str]]:
    case_id = str(uuid.uuid4())
    upload_prefix = f'uploads/{case_id}'
    case_dir = _case_staging_dir(case_id)
    os.makedirs(case_dir, exist_ok=True)

    staged_files = await asyncio.gather(
        *(_stage_single(name, file, case_dir) for name, file in files.items())
    )
    return case_id, upload_prefix, dict(staged_files)


def _upload_single(args):
    name, path, upload_prefix = args
    key = f'{upload_prefix}/{name}.nii'
    print(f'Uploading file key={key}')

    with open(path, 'rb') as file:
        _s3.upload_fileobj(file, S3_BUCKET, key)

    print(f'File uploaded key={key}')
    return name, _to_s3_uri(key)


def upload_staged_files(staged_files: dict[str, str], upload_prefix: str) -> dict[str, str]:
    with ThreadPoolExecutor(max_workers=8) as executor:
        args = [(name, path, upload_prefix) for name, path in staged_files.items()]
        s3_paths = executor.map(_upload_single, args)
        return {name: path for name, path in s3_paths}


def delete_staged_files(case_id: str) -> None:
    shutil.rmtree(_case_staging_dir(case_id), ignore_errors=True)


def uploaded_file_uri(upload_prefix: str, name: str) -> str:
    return _to_s3_uri(f'{upload_prefix}/{name}.nii')


def delete_scan_files(scan: type[Scan]):
    delete_staged_files(scan.case_id)
    for_deletion = [
        {'Key': f'{scan.upload_prefix}/{modality}.nii'}
        for modality in ('t1', 't1ce', 't2', 'flair', 'true_mask')
    ]
    if scan.result_path:
        for_deletion.append({'Key': _from_s3_uri(scan.result_path)})
    print(for_deletion)
    _s3.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': for_deletion})


@contextmanager
def local_paths_for_case(files_dict):
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_paths = {}
        for name, s3_uri in files_dict.items():
            key = _from_s3_uri(s3_uri)
            print(f'Local downloading key={key}')
            local_path = os.path.join(tmp_dir, f'{name}.nii')
            with open(local_path, 'wb') as output:
                _s3.download_fileobj(S3_BUCKET, key, output)
            print(f'Local downloaded key={key}')
            local_paths[name] = local_path
        yield local_paths


def save_result(case_id, prediction):
    key = f'results/{case_id}.npy'
    print(f'Uploading results key={key}')
    buffer = io.BytesIO()
    np.save(buffer, prediction)
    buffer.seek(0)
    _s3.upload_fileobj(buffer, S3_BUCKET, key)
    print(f'Results uploaded key={key}')
    return _to_s3_uri(key)


def load_result(result_uri: str) -> np.ndarray:
    key = _from_s3_uri(result_uri)
    print(f'Downloading results key={key}')
    buffer = io.BytesIO()
    _s3.download_fileobj(S3_BUCKET, key, buffer)
    buffer.seek(0)
    arr = np.load(buffer, allow_pickle=False)
    print(f'Results downloaded key={key}')
    return arr
