from aiokafka import AIOKafkaConsumer
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleCalendarSpec, ScheduleState, ScheduleRange
from datetime import datetime, timedelta, timezone
import json
from app.config import settings
from app.temporal_client import get_temporal_client

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


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
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

        try:
            if event_type == "appointment.created" and event.get("status") == "requested":
                appointment_id = event.get("appointment_id")
                if not appointment_id:
                    continue

                client = await get_temporal_client()
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

            elif event_type == "appointment.status_updated" and event.get("status") == "cancelled":
                appointment_id = event.get("appointment_id")
                if not appointment_id:
                    continue

                client = await get_temporal_client()
                for kind in ("day-before", "hour-before"):
                    try:
                        await client.get_schedule_handle(reminder_schedule_id(kind, appointment_id)).delete()
                    except Exception:
                        pass  # already fired and went inactive, or was never created

        except Exception:
            # one bad event shouldn't take the whole consumer loop down — log and keep going
            print(f"kafka_consumer: failed handling event_type={event_type}: {event}")
