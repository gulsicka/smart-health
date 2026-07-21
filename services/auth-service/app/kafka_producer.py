from aiokafka import AIOKafkaProducer
import json
from app.config import settings

producer: AIOKafkaProducer | None = None


async def start_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()


async def stop_producer():
    await producer.stop()


async def publish_user_deleted(user_id: int):
    await producer.send_and_wait(
        settings.KAFKA_TOPIC,
        value={"event_type": "user.deleted", "user_id": user_id},
        key=str(user_id).encode("utf-8"),
    )
