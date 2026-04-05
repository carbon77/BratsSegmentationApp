import asyncio
from dataclasses import dataclass

from app.db.database import SessionLocal
from app.db.models import Scan
from app.services.inference import run_inference
from app.services.preprocessing import preprocess_case, preprocess_true_mask
from app.services.results import compute_metrics
from app.services.storage import local_paths_for_case, save_result, save_uploaded_files_from_bytes_async


@dataclass
class PredictJob:
    case_id: str
    upload_prefix: str
    files: dict[str, bytes]


_job_queue: asyncio.Queue[PredictJob | None] = asyncio.Queue()
_worker_task: asyncio.Task | None = None


async def enqueue_predict_job(job: PredictJob):
    await _job_queue.put(job)


async def start_queue_worker():
    global _worker_task
    if _worker_task is None:
        _worker_task = asyncio.create_task(_worker_loop())


async def stop_queue_worker():
    global _worker_task
    if _worker_task is None:
        return

    await _job_queue.put(None)
    await _worker_task
    _worker_task = None


async def _worker_loop():
    while True:
        job = await _job_queue.get()
        if job is None:
            _job_queue.task_done()
            break
        try:
            await asyncio.to_thread(_process_predict_job, job)
        finally:
            _job_queue.task_done()


def _process_predict_job(job: PredictJob):
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.case_id == job.case_id).first()
        if not scan:
            return

        scan.status = 'processing'
        db.add(scan)
        db.commit()

        s3_paths = save_uploaded_files_from_bytes_async(job.files, job.upload_prefix)

        with local_paths_for_case(s3_paths) as local_paths:
            modality_paths = {modality: local_paths[modality] for modality in ('t1', 't1ce', 't2', 'flair')}
            tensor = preprocess_case(modality_paths)
            true_mask_volume = preprocess_true_mask(local_paths['true_mask']) if 'true_mask' in local_paths else None

        prediction = run_inference(tensor)
        metrics = compute_metrics(prediction, true_mask_volume)
        result_path = save_result(job.case_id, prediction)

        scan.status = 'completed'
        scan.result_path = result_path
        scan.metrics = metrics
        db.add(scan)
        db.commit()
    except Exception:
        scan = db.query(Scan).filter(Scan.case_id == job.case_id).first()
        if scan:
            scan.status = 'failed'
            db.add(scan)
            db.commit()
    finally:
        db.close()
