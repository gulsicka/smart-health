from aiokafka import AIOKafkaConsumer
import json
from app.config import settings
from app.database import SessionLocal
from app import crud, kafka_producer

consumer: AIOKafkaConsumer | None = None


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        settings.USERS_KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="patient-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()


async def stop_consumer():
    await consumer.stop()


async def consume_events():
    async for message in consumer:
        event = message.value
        if event.get("event_type") != "user.deleted":
            continue

        user_id = event.get("user_id")
        if not user_id:
            continue

        db = SessionLocal()
        try:
            patient = crud.soft_delete_patient_by_user_id(db, user_id)
            if patient:
                await kafka_producer.publish_patient_deleted(patient.id, user_id)
        finally:
            db.close()
