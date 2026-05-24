import base64
import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone
from urllib import error, request

from fastapi import HTTPException

ORTHANC_URL = os.getenv('ORTHANC_URL', 'http://orthanc:8042')
ORTHANC_USERNAME = os.getenv('ORTHANC_USERNAME', 'orthanc')
ORTHANC_PASSWORD = os.getenv('ORTHANC_PASSWORD', 'orthanc')


def _metrics_csv(metrics: dict) -> str:
    rows: list[tuple[str, object]] = []

    def flatten(node, prefix=''):
        if node is None:
            rows.append((prefix, ''))
            return

        if isinstance(node, dict):
            for key, value in node.items():
                next_prefix = f'{prefix}.{key}' if prefix else key
                flatten(value, next_prefix)
            return

        rows.append((prefix, node))

    flatten(metrics)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['metric', 'value'])
    for metric, value in rows:
        writer.writerow([metric, value])
    return buf.getvalue()


def _create_dicom_payload(case_id: str, title: str, content: str, content_type: str, file_name: str) -> bytes:
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
    body = {
        'Tags': {
            'PatientName': title,
            'PatientID': case_id,
            'StudyDescription': 'BraTS segmentation export',
            'SeriesDescription': content_type,
            'SOPClassUID': '1.2.840.10008.5.1.4.1.1.66',
            'SOPInstanceUID': f'2.25.{uuid.uuid4().int}',
        },
        'Content': encoded_content,
        'ContentType': 'application/octet-stream',
        'Encapsulate': True,
        'InterpretBinaryTags': False,
        'PrivateCreator': 'BratsSegmentationApp',
        'PrivateTags': {
            '0011,1010': file_name,
            '0011,1011': content_type,
        },
    }
    return json.dumps(body).encode('utf-8')


def _upload_to_orthanc(payload: bytes) -> None:
    upload_url = f'{ORTHANC_URL.rstrip("/")}/tools/create-dicom'
    http_request = request.Request(upload_url, data=payload, method='POST')
    http_request.add_header('Content-Type', 'application/json')
    auth = base64.b64encode(f'{ORTHANC_USERNAME}:{ORTHANC_PASSWORD}'.encode('utf-8')).decode('ascii')
    http_request.add_header('Authorization', f'Basic {auth}')

    try:
        with request.urlopen(http_request, timeout=20) as response:
            if response.status not in (200, 201):
                raise HTTPException(status_code=502, detail='Orthanc rejected the exported file')
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')
        raise HTTPException(status_code=502, detail=f'Orthanc HTTP error: {detail or exc.reason}') from exc
    except error.URLError as exc:
        raise HTTPException(status_code=502, detail='Orthanc is unavailable') from exc


def export_metrics_to_orthanc(case_id: str, title: str, metrics: dict) -> dict:
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    json_filename = f'{case_id}-metrics-{timestamp}.json'
    csv_filename = f'{case_id}-metrics-{timestamp}.csv'

    json_payload = json.dumps({'case_id': case_id, 'metrics': metrics}, ensure_ascii=False, indent=2)
    csv_payload = _metrics_csv(metrics)

    _upload_to_orthanc(_create_dicom_payload(case_id, title, json_payload, 'application/json', json_filename))
    _upload_to_orthanc(_create_dicom_payload(case_id, title, csv_payload, 'text/csv', csv_filename))

    return {
        'case_id': case_id,
        'exported': [json_filename, csv_filename],
        'orthanc_url': ORTHANC_URL,
    }
