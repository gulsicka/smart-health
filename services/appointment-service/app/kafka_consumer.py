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
        group_id="appointment-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()


async def stop_consumer():
    await consumer.stop()


async def consume_events():
    async for message in consumer:
        event = message.value
        event_type = event.get("event_type")

        db = SessionLocal()
        try:
            if event_type == "patient.deleted":
                patient_id = event.get("patient_id")
                if patient_id:
                    crud.cancel_appointments_by_patient_id(db, patient_id)
            elif event_type == "provider.deleted":
                provider_id = event.get("provider_id")
                if provider_id:
                    crud.cancel_appointments_by_provider_id(db, provider_id)
        finally:
            db.close()
