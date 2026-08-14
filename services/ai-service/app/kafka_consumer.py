from aiokafka import AIOKafkaConsumer
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleCalendarSpec, ScheduleState, ScheduleRange
from datetime import datetime, timedelta, timezone
import json
from app.config import settings
from app.database import SessionLocal
from app.temporal_client import get_temporal_client
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


def reminder_schedule_id(kind: str, appointment_id) -> str:
    return f"appointment-reminder-{kind}-{appointment_id}"


async def create_reminder_schedule(client, workflow_name: str, schedule_id: str, data: dict, fire_at: datetime):
    await client.create_schedule(
        schedule_id,
        Schedule(
            action=ScheduleActionStartWorkflow(
                workflow_name,
                data,
                id=schedule_id,
                task_queue=settings.REMINDER_TASK_QUEUE,
            ),
            spec=ScheduleSpec(
                calendars=[
                    ScheduleCalendarSpec(
                        year=[ScheduleRange(fire_at.year)],
                        month=[ScheduleRange(fire_at.month)],
                        day_of_month=[ScheduleRange(fire_at.day)],
                        hour=[ScheduleRange(fire_at.hour)],
                        minute=[ScheduleRange(fire_at.minute)],
                    )
                ]
            ),
            state=ScheduleState(limited_actions=True, remaining_actions=1),
        ),
    )


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
                    appointment_id = event.get("appointment_id")
                    reminder_data = {
                        "appointment_id": appointment_id,
                        "patient_id": event.get("patient_id"),
                        "provider_id": event.get("provider_id"),
                        "clinic_id": event.get("clinic_id"),
                        "date": event.get("date"),
                        "start_time": event.get("start_time"),
                        "end_time": event.get("end_time"),
                    }

                    date_parts = [int(x) for x in event["date"].split("-")]
                    time_parts = [int(x) for x in event["start_time"].split(":")]
                    appt_datetime = datetime(date_parts[0], date_parts[1], date_parts[2], time_parts[0], time_parts[1], tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)

                    day_before = appt_datetime - timedelta(days=1)
                    if day_before > now:  # skip if already in the past
                        await create_reminder_schedule(
                            client, "SendDayBeforeReminderWorkflow",
                            reminder_schedule_id("day-before", appointment_id), reminder_data, day_before,
                        )

                    hour_before = appt_datetime - timedelta(hours=1)  
                    if hour_before > now:
                        await create_reminder_schedule(
                            client, "SendHourBeforeReminderWorkflow",
                            reminder_schedule_id("hour-before", appointment_id), reminder_data, hour_before,
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

                if event.get("status") == "cancelled":
                    client = await get_temporal_client()
                    appointment_id = event.get("appointment_id")
                    for kind in ("day-before", "hour-before"):
                        try:
                            await client.get_schedule_handle(reminder_schedule_id(kind, appointment_id)).delete()
                        except Exception:
                            pass  #  hour_before already past at booking time

        finally:
            db.close()
