from http.client import HTTPException

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.db.models import Scan
from app.services.inference import run_inference
from app.services.preprocessing import preprocess_case
from app.services.storage import save_uploaded_files, save_result

router = APIRouter()


@router.post("/predict")
async def predict(
        t1: UploadFile = File(...),
        t1ce: UploadFile = File(...),
        t2: UploadFile = File(...),
        flair: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    files = {
        "t1": t1,
        "t1ce": t1ce,
        "t2": t2,
        "flair": flair,
    }
    case_id, paths = save_uploaded_files(files)

    scan = Scan(case_id=case_id, upload_prefix=case_id, status='uploaded')
    db.add(scan)
    db.commit()

    tensor = preprocess_case(paths)
    prediction = run_inference(tensor)
    result_path = save_result(case_id, prediction)
    return {
        "case_id": case_id,
        "result_path": result_path,
    }


@router.get('/scans/{case_id}')
async def get_scan(case_id: str, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.case_id == case_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="scan not found")
    return {
        'case_id': scan.case_id,
        'upload_predix': scan.upload_prefix,
        'status': scan.status,
    }
