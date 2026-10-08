from datetime import datetime
from aiokafka import AIOKafkaConsumer
import redis.asyncio as aioredis
import json
from .config import settings
from .celery_client import notify_user
from .user_lookup import get_patient_user_id, get_provider_user_id
from app.crud.appointments import insert_event
from app.crud.ai_events import insert_ai_event

consumer: AIOKafkaConsumer | None = None
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def notify_appointment_parties(event: dict, notification_type: str, message: str):
    # notifications are stored against user ids, so translate the patient and
    # provider ids on the event to their user ids; both parties are told
    user_ids = {
        await get_patient_user_id(event.get("patient_id")),
        await get_provider_user_id(event.get("provider_id")),
    }
    for user_id in user_ids - {None}:
        notify_user(user_id, event.get("appointment_id"), notification_type, message)


async def handle_event(event: dict):
    event_type = event.get("event_type")
    status = event.get("status")
    date = datetime.now().date().isoformat()
    patient_id = event.get("patient_id")
    appointment_id = event.get("appointment_id")

    if event_type == "patient.created":
        await redis_client.incr("analytics:total_patients")

    elif event_type == "appointment.created":
        await redis_client.incr("analytics:total_appointments")
        await redis_client.hincrby("analytics:daily_bookings", date, 1)
        insert_event(event, event_type) #time scale db record insertion

    elif event_type == "appointment.status_updated":
        if status == "checked_in":
            # store check-in time to compute wait duration when visit starts
            await redis_client.set(
                f"analytics:checkin_time:{appointment_id}",
                datetime.now().isoformat(),
                ex=86400,  # expire after 24h in case in_progress never fires
            )
            insert_event(event, "appointment.checked_in")

        elif status == "in_progress":
            checkin_raw = await redis_client.get(f"analytics:checkin_time:{appointment_id}")
            if checkin_raw:
                checkin_time = datetime.fromisoformat(checkin_raw)
                wait_minutes = (datetime.now() - checkin_time).total_seconds() / 60
                await redis_client.incrbyfloat("analytics:total_wait_minutes", wait_minutes)
                await redis_client.incr("analytics:wait_time_count")
                await redis_client.delete(f"analytics:checkin_time:{appointment_id}")
                insert_event(event, "appointment.in_progress")
                
        elif status == "completed":
            await redis_client.incr("analytics:total_completed")
            await redis_client.hincrby("analytics:daily_completions", date, 1)
            insert_event(event, "appointment.completed")
            
        elif status == "confirmed":
            await notify_appointment_parties(
                event,
                "booking_confirmation",
                f"Appointment {appointment_id} on {event.get('date')} at {str(event.get('start_time'))[:5]} has been confirmed.",
            )
            insert_event(event, "appointment.confirmed")

        elif status == "cancelled":
            await redis_client.incr("analytics:total_cancelled")
            await redis_client.hincrby("analytics:daily_cancellations", date, 1)
            await notify_appointment_parties(
                event,
                "appointment_cancellation",
                f"Appointment {appointment_id} on {event.get('date')} at {str(event.get('start_time'))[:5]} "
                f"was cancelled by {event.get('changed_by', 'clinic staff')}.",
            )
            insert_event(event, "appointment.cancelled") #time scale db record insertion

    elif event_type in ("ai.chat", "ai.communication", "ai.report"):
        ai_status = event.get("status", "unknown")

        await redis_client.incr("analytics:ai_usage:total")
        await redis_client.incr(f"analytics:ai_usage:{event_type}")

        if event_type == "ai.chat":                                            
            await redis_client.incr(f"analytics:ai_chat:{ai_status}")

        elif event_type == "ai.communication":
            comm_type = event.get("communication_type", "unknown")
            await redis_client.incr(f"analytics:ai_communication:{comm_type}:{ai_status}")

        insert_ai_event(event, event_type) #time scale db record insertion


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        settings.PATIENT_KAFKA_TOPIC,
        settings.AI_KAFKA_TOPIC,
        bootstrap_servers="kafka:9092",
        group_id="analytics-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()
    
async def stop_consumer():
    await consumer.stop()
    
async def consume_events():
    async for message in consumer:
        event = message.value
        event_id = event.get("event_id")
        
        is_new = await redis_client.set(f"dedupe:{event_id}", 1, nx=True, ex=86400)
        if not is_new:
            continue  # already processed, skip
        try:
            await handle_event(event)
        except Exception as e:
            print(f"Error handling event: {e}")
        
        # Process the event here
        print(f"Consumed event: {event}")