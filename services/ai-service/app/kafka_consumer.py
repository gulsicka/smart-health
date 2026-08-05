from aiokafka import AIOKafkaConsumer
import json
from app.config import settings
from app.database import SessionLocal
from app import crud
from app.utils.event_text import event_to_text, provider_full_text, patient_full_text
from app.clients import provider, patients, appointment

consumer: AIOKafkaConsumer | None = None


def get_source(event: dict) -> str | None:
    event_type = event.get("event_type", "")
    if "provider" in event_type:
        id_ = event.get("provider_id")
        return f"provider-{id_}" if id_ else None
    if "patient" in event_type:
        id_ = event.get("patient_id")
        return f"patient-{id_}" if id_ else None
    if "appointment" in event_type:
        id_ = event.get("appointment_id")
        return f"appointment-{id_}" if id_ else None
    return None


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        settings.PROVIDER_KAFKA_TOPIC,
        settings.PATIENT_KAFKA_TOPIC,
        settings.APPOINTMENT_KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="ai-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()


async def stop_consumer():
    await consumer.stop()


async def consume_events():
    async for message in consumer:
        event = message.value
        event_type = event.get("event_type")
        source = get_source(event)

        if not source:
            continue

        db = SessionLocal()
        try:
            if event_type == "provider.created":
                provider_data = await provider.get_provider(event["provider_id"])
                text = provider_full_text(provider_data)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])
            elif event_type == "patient.created":
                patient_data = await patients.get_patient(event["patient_id"])
                text = patient_full_text(patient_data)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text]) 
            else:
                text = event_to_text(event)
                if not text:
                    continue
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])
        finally:
            db.close()
