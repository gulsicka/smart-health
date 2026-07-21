from aiokafka import AIOKafkaConsumer
import json
from app.config import settings
from app.database import SessionLocal
from app import crud

consumer: AIOKafkaConsumer | None = None


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        settings.PATIENT_KAFKA_TOPIC,
        settings.PROVIDER_KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="auth-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()


async def stop_consumer():
    await consumer.stop()


async def consume_events():
    async for message in consumer:
        event = message.value
        event_type = event.get("event_type")
        user_id = event.get("user_id")

        if not user_id:
            continue

        if event_type == "patient.deleted":
            db = SessionLocal()
            try:
                user = crud.get_user_by_id(db, user_id)
                if user:
                    crud.remove_user_roles(db, user, ["patient"])
            finally:
                db.close()

        elif event_type == "provider.deleted":
            db = SessionLocal()
            try:
                user = crud.get_user_by_id(db, user_id)
                if user:
                    crud.remove_user_roles(db, user, ["provider"])
            finally:
                db.close()
