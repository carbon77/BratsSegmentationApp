import asyncio
import json

from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm.session import Session

from app.db.database import get_db, SessionLocal
from app.db.models import Scan
from app.dto.dto import PatchScanRequest
from app.services.preprocessing import preprocess_modality_slice
from app.services.results import get_slice_plot
from app.services.storage import stage_uploaded_files, local_paths_for_case, load_result, \
    delete_scan_files, delete_staged_files, uploaded_file_uri
from app.services.tasks import enqueue_segmentation_task

router = APIRouter()

MODALITIES = ('t1', 't1ce', 't2', 'flair')


def _scan_to_dict(scan: Scan) -> dict:
    return {
        'case_id': scan.case_id,
        'title': scan.title,
        'status': scan.status,
    }


@router.post('/predict', status_code=202)
async def predict(
        t1: UploadFile = File(...),
        t1ce: UploadFile = File(...),
        t2: UploadFile = File(...),
        flair: UploadFile = File(...),
        true_mask: UploadFile | None = File(None),
        db: Session = Depends(get_db)
):
    files = {
        't1': t1,
        't1ce': t1ce,
        't2': t2,
        'flair': flair,
    }
    if true_mask is not None:
        files['true_mask'] = true_mask

    print('Staging uploaded files...')
    case_id, upload_prefix, staged_files = await stage_uploaded_files(files)
    print('Files staged!')

    scan = Scan(case_id=case_id, title=case_id, upload_prefix=upload_prefix, status='uploading')
    db.add(scan)
    db.commit()

    try:
        await enqueue_segmentation_task(case_id, upload_prefix, staged_files)
    except Exception as exc:
        delete_staged_files(case_id)
        scan.status = 'failed'
        db.add(scan)
        db.commit()
        raise HTTPException(status_code=503, detail='Could not enqueue upload task') from exc

    return _scan_to_dict(scan)


@router.get('/scans/{case_id}/result/metrics')
async def result_metrics(case_id: str, db: Session = Depends(get_db)):
    scan = _get_scan(db, case_id)
    if scan.status != 'completed' or not scan.metrics:
        raise HTTPException(status_code=400, detail='Scan results not ready')
    return {
        'case_id': case_id,
        'metrics': scan.metrics,
    }


@router.get('/scans')
async def get_scans(db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(Scan.created_at.desc()).all()
    return [_scan_to_dict(scan) for scan in scans]


@router.get('/scans/events')
async def scan_events():
    async def event_stream():
        last_payload = None
        while True:
            with SessionLocal() as db:
                scans = db.query(Scan).order_by(Scan.created_at.desc()).all()
                payload = json.dumps([_scan_to_dict(scan) for scan in scans])

            if payload != last_payload:
                yield f'event: scans\ndata: {payload}\n\n'
                last_payload = payload

            await asyncio.sleep(2)

    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@router.get('/scans/{case_id}/result/images')
async def result_images(
        case_id: str,
        slice_idx: int = Query(1, ge=0, description='Slice index to return.'),
        overlay_modality: str | None = Query(
            None,
            description='MRI modality to draw underneath the segmentation mask. Omit for mask only.',
        ),
        db: Session = Depends(get_db),
):
    scan = _get_scan(db, case_id)
    if scan.status != 'completed' or not scan.result_path:
        raise HTTPException(status_code=400, detail='Scan result not ready')

    if overlay_modality is not None and overlay_modality not in MODALITIES:
        raise HTTPException(
            status_code=400,
            detail=f'overlay_modality must be one of: {", ".join(MODALITIES)}',
        )

    prediction = load_result(scan.result_path)
    volume = prediction[0] if prediction.ndim == 4 else prediction
    if slice_idx >= volume.shape[0]:
        raise HTTPException(status_code=400, detail=f'slice_idx must be between 0 and {volume.shape[0] - 1}')

    background_slice = None
    if overlay_modality is not None:
        modality_uri = uploaded_file_uri(scan.upload_prefix, overlay_modality)
        with local_paths_for_case({overlay_modality: modality_uri}) as local_paths:
            try:
                background_slice = preprocess_modality_slice(local_paths[overlay_modality], slice_idx)
            except IndexError as exc:
                raise HTTPException(status_code=400, detail='slice_idx is outside the uploaded MRI volume') from exc

    buf = get_slice_plot(prediction, slice_idx, background_slice, overlay_modality)
    buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')


@router.delete('/scans/{case_id}')
async def delete_scan(case_id: str, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.case_id == case_id).first()
    if scan:
        delete_scan_files(scan)
        db.delete(scan)
        db.commit()
    return Response(status_code=204)


@router.patch('/scans/{case_id}')
async def patch_scan(
        case_id: str,
        request: PatchScanRequest,
        db: Session = Depends(get_db),
):
    scan = _get_scan(db, case_id)
    scan.title = request.title
    db.add(scan)
    db.commit()
    return Response(status_code=204)


def _get_scan(db: Session, case_id: str) -> type[Scan]:
    scan = db.query(Scan).filter(Scan.case_id == case_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail='scan not found')
    return scan
