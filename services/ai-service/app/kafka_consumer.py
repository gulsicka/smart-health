from aiokafka import AIOKafkaConsumer
from temporalio.client import Client
import json
from app.config import settings
from app.database import SessionLocal
from app import crud
from app.utils.event_text import event_to_text, provider_full_text, patient_full_text
from app.clients import provider, patients

consumer: AIOKafkaConsumer | None = None
_temporal_client: Client | None = None


async def get_temporal_client() -> Client:
    global _temporal_client
    if _temporal_client is None:
        _temporal_client = await Client.connect(settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE)
    return _temporal_client


def get_source(event: dict) -> str | None:
    event_type = event.get("event_type", "")
    if "provider" in event_type:
        id_ = event.get("provider_id")
        return f"provider-{id_}" if id_ else None
    if "patient" in event_type:
        id_ = event.get("patient_id")
        return f"patient-{id_}" if id_ else None
    if "appointment" in event_type:
        appt_id = event.get("appointment_id")
        patient_id = event.get("patient_id")
        provider_id = event.get("provider_id")
        clinic_id = event.get("clinic_id")
        if not appt_id:
            return None
        return f"patient-{patient_id}-provider-{provider_id}-clinic-{clinic_id}-appointment-{appt_id}"
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

            elif event_type == "appointment.created":
                text = event_to_text(event)
                if text:
                    crud.delete_chunks(db, source)
                    crud.ingest_chunks(db, source, [text])

                if event.get("status") == "requested": #scheduling reminders for requested appointments only
                    client = await get_temporal_client()
                    await client.start_workflow(
                        "AppointmentReminderWorkflow",
                        {
                            "appointment_id": event.get("appointment_id"),
                            "patient_id": event.get("patient_id"),
                            "provider_id": event.get("provider_id"),
                            "clinic_id": event.get("clinic_id"),
                            "date": event.get("date"),
                            "start_time": event.get("start_time"),
                            "end_time": event.get("end_time"),
                        },
                        id=f"appointment-reminder-{event.get('appointment_id')}",
                        task_queue=settings.REMINDER_TASK_QUEUE,
                    )

            elif event_type == "appointment.status_updated" and event.get("status") == "cancelled":
                text = event_to_text(event)
                if text:
                    crud.delete_chunks(db, source)
                    crud.ingest_chunks(db, source, [text])

                try:
                    client = await get_temporal_client()
                    handle = client.get_workflow_handle(f"appointment-reminder-{event.get('appointment_id')}")
                    await handle.signal("cancel") #cancel reminder
                except Exception:
                    pass 

            else:
                text = event_to_text(event)
                if not text:
                    continue
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

        finally:
            db.close()
