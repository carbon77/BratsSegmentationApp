import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

from app.db.database import SessionLocal, engine
from app.db.models import Base, Scan
from app.services.segmentation import process_segmentation
from app.services.storage import delete_staged_files, upload_staged_files
from app.services.tasks import KAFKA_BOOTSTRAP_SERVERS, SEGMENTATION_TOPIC

load_dotenv()

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

CONSUMER_GROUP = os.getenv('SEGMENTATION_CONSUMER_GROUP', 'segmentation-workers')


def _mark_status(case_id: str, status: str) -> None:
    with SessionLocal() as db:
        scan = db.query(Scan).filter(Scan.case_id == case_id).first()
        if scan:
            scan.status = status
            db.add(scan)
            db.commit()


def _mark_completed(case_id: str, result_path: str, metrics: dict) -> None:
    with SessionLocal() as db:
        scan = db.query(Scan).filter(Scan.case_id == case_id).first()
        if scan:
            scan.status = 'completed'
            scan.result_path = result_path
            scan.metrics = metrics
            db.add(scan)
            db.commit()


async def _handle_message(payload: dict) -> None:
    case_id = payload['case_id']
    upload_prefix = payload['upload_prefix']
    staged_files = payload['staged_files']
    logger.info('Starting upload task case_id=%s', case_id)

    try:
        s3_paths = await asyncio.to_thread(upload_staged_files, staged_files, upload_prefix)
        await asyncio.to_thread(_mark_status, case_id, 'processing')
        logger.info('Starting segmentation task case_id=%s', case_id)
        result_path, metrics = await asyncio.to_thread(process_segmentation, case_id, s3_paths)
    except Exception:
        logger.exception('Upload or segmentation task failed case_id=%s', case_id)
        await asyncio.to_thread(_mark_status, case_id, 'failed')
        return
    finally:
        await asyncio.to_thread(delete_staged_files, case_id)

    await asyncio.to_thread(_mark_completed, case_id, result_path, metrics)
    logger.info('Segmentation task completed case_id=%s', case_id)


async def main() -> None:
    Base.metadata.create_all(bind=engine)
    consumer = AIOKafkaConsumer(
        SEGMENTATION_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda value: json.loads(value.decode('utf-8')),
        enable_auto_commit=False,
    )
    await consumer.start()
    try:
        async for message in consumer:
            await _handle_message(message.value)
            await consumer.commit()
    finally:
        await consumer.stop()


if __name__ == '__main__':
    asyncio.run(main())
