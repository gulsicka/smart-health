from datetime import date, datetime
from celery import Celery

from aiokafka import AIOKafkaConsumer
import redis.asyncio as aioredis
import json
from .config import settings

consumer: AIOKafkaConsumer | None = None
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
celery_app = Celery("analytics_service", broker=settings.RABBITMQ_URL)

async def handle_event(event: dict):
    event_type = event.get("event_type")
    status = event.get("status")
    date = datetime.now().date().isoformat()
    patient_id = event.get("patient_id")
    appointment_id = event.get("appointment_id")

    if event_type == "appointment.created":
        await redis_client.incr("analytics:total_appointments")
        await redis_client.hincrby("analytics:daily_bookings", date, 1)
        celery_app.send_task("tasks.send_booking_confirmation", args=[patient_id, appointment_id])

    elif event_type == "appointment.status_updated":
        if status == "completed":
            await redis_client.incr("analytics:total_completed")
            await redis_client.hincrby("analytics:daily_completions", date, 1)
        elif status == "confirmed":
            celery_app.send_task("tasks.send_booking_confirmation", args=[patient_id, appointment_id])
        elif status == "cancelled":
            await redis_client.incr("analytics:total_cancelled")
            await redis_client.hincrby("analytics:daily_cancellations", date, 1)
            celery_app.send_task("tasks.send_appointment_cancellation", args=[patient_id, appointment_id])


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers="kafka:9092",
        group_id="analytics-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),  # value_deserializer converts json bytes to dict after receiving from Kafka
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
        
        await handle_event(event)
        
        # Process the event here
        print(f"Consumed event: {event}")