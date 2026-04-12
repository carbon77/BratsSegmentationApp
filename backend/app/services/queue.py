import asyncio
from dataclasses import dataclass

from app.db.database import SessionLocal
from app.db.models import Scan
from app.services.inference import run_inference
from app.services.preprocessing import preprocess_case, preprocess_true_mask
from app.services.results import compute_metrics
from app.services.storage import local_paths_for_case, save_result


@dataclass
class ScanJob:
    case_id: str
    s3_paths: dict[str, str]


_scan_queue: asyncio.Queue[ScanJob] = asyncio.Queue()
_worker_task: asyncio.Task | None = None


def enqueue_scan_job(job: ScanJob):
    _scan_queue.put_nowait(job)


async def run_scan_worker():
    while True:
        job = await _scan_queue.get()
        try:
            await _process_scan_job(job)
        except Exception:
            db = SessionLocal()
            try:
                scan = db.query(Scan).filter(Scan.case_id == job.case_id).first()
                if scan:
                    scan.status = 'failed'
                    db.add(scan)
                    db.commit()
            finally:
                db.close()
        finally:
            _scan_queue.task_done()


async def _process_scan_job(job: ScanJob):
    prediction, metrics, result_path = await asyncio.to_thread(_process_scan_job_sync, job)

    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.case_id == job.case_id).first()
        if not scan:
            return
        scan.status = 'completed'
        scan.result_path = result_path
        scan.metrics = metrics
        db.add(scan)
        db.commit()
    finally:
        db.close()


def _process_scan_job_sync(job: ScanJob):
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.case_id == job.case_id).first()
        if scan:
            scan.status = 'processing'
            db.add(scan)
            db.commit()
    finally:
        db.close()

    with local_paths_for_case(job.s3_paths) as local_paths:
        modality_paths = {modality: local_paths[modality] for modality in ('t1', 't1ce', 't2', 'flair')}
        tensor = preprocess_case(modality_paths)
        true_mask_volume = preprocess_true_mask(local_paths['true_mask']) if 'true_mask' in local_paths else None

    prediction = run_inference(tensor)
    metrics = compute_metrics(prediction, true_mask_volume)
    result_path = save_result(job.case_id, prediction)
    return prediction, metrics, result_path


async def start_scan_worker():
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(run_scan_worker())


async def stop_scan_worker():
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
