from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.db.models import Scan
from app.dto.dto import PatchScanRequest
from app.services.inference import run_inference
from app.services.preprocessing import preprocess_case, preprocess_true_mask, preprocess_modality_slice
from app.services.results import compute_metrics, get_slice_plot
from app.services.storage import save_uploaded_files_async, local_paths_for_case, save_result, load_result, \
    delete_scan_files, uploaded_file_uri

router = APIRouter()

MODALITIES = ('t1', 't1ce', 't2', 'flair')


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

    print(f'Uploading files...')
    case_id, upload_prefix, s3_paths = save_uploaded_files_async(files)
    print(f'Files uploaded!')

    scan = Scan(case_id=case_id, title=case_id, upload_prefix=upload_prefix, status='uploaded')
    db.add(scan)
    db.commit()

    print('Preprocessing files...')
    with local_paths_for_case(s3_paths) as local_paths:
        modality_paths = {modality: local_paths[modality] for modality in MODALITIES}
        tensor = preprocess_case(modality_paths)
        true_mask_volume = preprocess_true_mask(local_paths['true_mask']) if 'true_mask' in local_paths else None
    prediction = run_inference(tensor)
    metrics = compute_metrics(prediction, true_mask_volume)
    result_path = save_result(case_id, prediction)
    print('Files processed!')

    scan.status = 'completed'
    scan.result_path = result_path
    scan.metrics = metrics
    db.add(scan)
    db.commit()

    return {
        'case_id': case_id,
        'result_path': result_path,
        'metrics': metrics,
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
    return StreamingResponse(buf, media_type="image/png")


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
        raise HTTPException(status_code=404, detail="scan not found")
    return scan
