from aiokafka import AIOKafkaConsumer
from temporalio.client import Client
import json
from app.config import settings
from app.database import SessionLocal
from app import crud
from app.utils.event_text import (
    patient_full_text,
    patient_deleted_text,
    provider_full_text,
    provider_deleted_text,
    appointment_full_text,
    appointment_status_updated_text,
)
from app.clients import provider as provider_client, patients as patients_client
from app.clients import auth as auth_client

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


async def fetch_appointment_context(event: dict) -> tuple:
    """Returns (patient_name, provider_name, dept_name, clinic_data) for an appointment event."""
    patient_data = await patients_client.get_patient(event["patient_id"])
    patient_user = await auth_client.get_user(patient_data["user_id"])
    provider_data = await provider_client.get_provider(event["provider_id"])
    provider_user = await auth_client.get_user(provider_data["user_id"])
    dept_data = await provider_client.get_department(provider_data["department_id"])
    clinic_data = await provider_client.get_clinic(event["clinic_id"])
    return (
        patient_user.get("name", "Unknown"),
        provider_user.get("name", "Unknown"),
        dept_data.get("name", "Unknown"),
        clinic_data,
    )


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
                provider_data = await provider_client.get_provider(event["provider_id"])
                user_data = await auth_client.get_user(provider_data["user_id"])
                dept_data = await provider_client.get_department(provider_data["department_id"])
                text = provider_full_text(provider_data, user_data, dept_data)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

            elif event_type == "provider.deleted":
                try:
                    provider_data = await provider_client.get_provider(event["provider_id"])
                    user_data = await auth_client.get_user(provider_data["user_id"])
                    provider_name = user_data.get("name", "Unknown")
                except Exception:
                    provider_name = "Unknown"
                text = provider_deleted_text(event, provider_name)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

            elif event_type == "patient.created":
                patient_data = await patients_client.get_patient(event["patient_id"])
                user_data = await auth_client.get_user(patient_data["user_id"])
                text = patient_full_text(patient_data, user_data)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

            elif event_type == "patient.deleted":
                try:
                    patient_data = await patients_client.get_patient(event["patient_id"])
                    user_data = await auth_client.get_user(patient_data["user_id"])
                    patient_name = user_data.get("name", "Unknown")
                except Exception:
                    patient_name = "Unknown"
                text = patient_deleted_text(event, patient_name)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

            elif event_type == "appointment.created":
                patient_name, provider_name, dept_name, clinic_data = await fetch_appointment_context(event)
                text = appointment_full_text(event, patient_name, provider_name, dept_name, clinic_data)
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

                if event.get("status") == "requested":  # scheduling reminders for requested appointments only
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

            elif event_type == "appointment.status_updated":
                patient_name, provider_name, _, clinic_data = await fetch_appointment_context(event)
                text = appointment_status_updated_text(
                    event,
                    patient_name,
                    provider_name,
                    clinic_data.get("name", "Unknown"),
                )
                crud.delete_chunks(db, source)
                crud.ingest_chunks(db, source, [text])

                if event.get("status") == "cancelled":  # cancel reminder workflow
                    try:
                        client = await get_temporal_client()
                        handle = client.get_workflow_handle(f"appointment-reminder-{event.get('appointment_id')}")
                        await handle.signal("cancel")
                    except Exception:
                        pass

        finally:
            db.close()
