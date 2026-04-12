import asyncio

from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.db.models import Scan
from app.dto.dto import PatchScanRequest
from app.services.queue import enqueue_scan_job, ScanJob
from app.services.results import get_slice_plot
from app.services.storage import save_uploaded_files_async, load_result, delete_scan_files

router = APIRouter()


@router.post("/predict")
async def predict(
        t1: UploadFile = File(...),
        t1ce: UploadFile = File(...),
        t2: UploadFile = File(...),
        flair: UploadFile = File(...),
        true_mask: UploadFile | None = File(None),
        db: Session = Depends(get_db)
):
    files = {
        "t1": t1,
        "t1ce": t1ce,
        "t2": t2,
        "flair": flair,
    }
    if true_mask is not None:
        files['true_mask'] = true_mask

    case_id, upload_prefix, s3_paths = await asyncio.to_thread(save_uploaded_files_async, files)

    scan = Scan(case_id=case_id, title=case_id, upload_prefix=upload_prefix, status='queued')
    db.add(scan)
    db.commit()

    enqueue_scan_job(ScanJob(case_id=case_id, s3_paths=s3_paths))

    return {
        'case_id': case_id,
        'status': 'queued',
    }


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
    scans = db.query(Scan).all()
    return [{
        'case_id': scan.case_id,
        'title': scan.title,
        'status': scan.status,
    } for scan in scans]


@router.get('/scans/{case_id}/result/images')
async def result_images(
        case_id: str,
        slice_idx: int = Query(1, description='Slice index to return.'),
        db: Session = Depends(get_db),
):
    scan = _get_scan(db, case_id)
    if scan.status != 'completed' or not scan.result_path:
        raise HTTPException(status_code=400, detail='Scan result not ready')

    prediction = await asyncio.to_thread(load_result, scan.result_path)
    buf = get_slice_plot(prediction, slice_idx)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.delete('/scans/{case_id}')
async def delete_scan(case_id: str, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.case_id == case_id).first()
    if scan:
        await asyncio.to_thread(delete_scan_files, scan)
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
        raise HTTPException(status_code=404, detail="scan not found")
    return scan
