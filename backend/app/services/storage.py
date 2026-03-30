import io
import os
import tempfile
import uuid
from contextlib import contextmanager

import boto3
import numpy as np

S3_BUCKET = os.getenv('S3_BUCKET', 'brats')
AWS_REGION = os.getenv('AWS_REGION', 'ru-central1')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'https://storage.yandexcloud.net')

_s3 = boto3.client('s3', region_name=AWS_REGION, endpoint_url=AWS_S3_ENDPOINT_URL)


def _to_s3_uri(key: str) -> str:
    return f's3://{S3_BUCKET}/{key}'


def _from_s3_uri(uri: str) -> str:
    expected_prefix = f's3://{S3_BUCKET}'
    if not uri.startswith(expected_prefix):
        raise ValueError(f'Invalid S3 URI: {uri}')
    return uri.removeprefix(expected_prefix)


def save_uploaded_files(files):
    print(f'Saving files to {S3_BUCKET}')

    case_id = str(uuid.uuid4())
    upload_prefix = f'uploads/{case_id}'
    paths = {}

    for name, file in files.items():
        key = f'{upload_prefix}/{name}.nii'
        _s3.upload_fileobj(file.file, S3_BUCKET, key)
        paths[name] = _to_s3_uri(key)
        file.file.seek(0)
    return case_id, upload_prefix, paths


@contextmanager
def local_paths_for_case(files_dict):
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_paths = {}
        for name, s3_uri in files_dict.items():
            key = _from_s3_uri(s3_uri)
            local_path = os.path.join(tmp_dir, f'{name}.nii')
            with open(local_path, 'wb') as output:
                _s3.download_fileobj(S3_BUCKET, key, output)
            local_paths[name] = local_path
        yield local_paths


def save_result(case_id, prediction):
    key = f'results/{case_id}.npy'
    buffer = io.BytesIO()
    np.save(buffer, prediction)
    buffer.seek(0)
    _s3.upload_fileobj(buffer, S3_BUCKET, key)
    return _to_s3_uri(key)


def load_result(result_uri: str):
    key = _from_s3_uri(result_uri)
    buffer = io.BytesIO()
    _s3.download_fileobj(S3_BUCKET, key, buffer)
    buffer.seek(0)
    return np.load(buffer, allow_pickle=False)
