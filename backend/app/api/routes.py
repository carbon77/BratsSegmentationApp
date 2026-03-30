from fastapi import APIRouter, UploadFile, File

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
):
    files = {
        "t1": t1,
        "t1ce": t1ce,
        "t2": t2,
        "flair": flair,
    }
    case_id, paths = save_uploaded_files(files)

    tensor = preprocess_case(paths)
    prediction = run_inference(tensor)
    result_path = save_result(case_id, prediction)
    return {
        "case_id": case_id,
        "result_path": result_path,
    }