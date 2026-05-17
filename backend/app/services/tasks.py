import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
SEGMENTATION_TOPIC = os.getenv('SEGMENTATION_TOPIC', 'segmentation-tasks')

_producer = None


async def start_task_producer() -> None:
    global _producer
    if _producer is None:
        from aiokafka import AIOKafkaProducer

        _producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode('utf-8'),
        )
        await _producer.start()


async def stop_task_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None


async def enqueue_segmentation_task(case_id: str, upload_prefix: str, staged_files: dict[str, str]) -> None:
    if _producer is None:
        await start_task_producer()
    await _producer.send_and_wait(
        SEGMENTATION_TOPIC,
        {
            'case_id': case_id,
            'upload_prefix': upload_prefix,
            'staged_files': staged_files,
        },
        key=case_id.encode('utf-8'),
    )
