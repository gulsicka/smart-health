from aiokafka import AIOKafkaConsumer
import redis.asyncio as aioredis
import json
from app.config import settings
from app.database import SessionLocal
from app import crud
from app.enums import InvoiceStatus

consumer: AIOKafkaConsumer | None = None
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def start_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="billing-service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()


async def stop_consumer():
    await consumer.stop()


async def consume_events():
    async for message in consumer:
        event = message.value
        event_type = event.get("event_type")
        event_id = event.get("event_id")

        if not event_id:
            continue

        #idempotency
        is_new = await redis_client.set(
            f"billing:event:{event_id}", "1", nx=True, ex=86400
        )
        if not is_new:
            continue

        if event_type == "appointment.created":
            db = SessionLocal()
            try:
                appointment_id = event.get("appointment_id")
                existing = crud.get_invoice_by_appointment(db, appointment_id)
                if existing:
                    continue
                crud.create_invoice(
                    db,
                    appointment_id=appointment_id,
                    patient_id=event.get("patient_id"),
                    provider_id=event.get("provider_id"),
                    clinic_id=event.get("clinic_id"),
                    amount=settings.CONSULTATION_FEE,
                    appointment_date=event.get("date"),
                )
                print(f"[billing] Invoice created for appointment {appointment_id}")
            except Exception as e:
                print(f"[billing] Failed to create invoice: {e}")
            finally:
                db.close()

        elif event_type == "appointment.status_updated":
            status = event.get("status")
            appointment_id = event.get("appointment_id")

            if status not in ("completed", "cancelled", "no_show"):
                continue

            db = SessionLocal()
            try:
                invoice = crud.get_invoice_by_appointment(db, appointment_id)
                if not invoice:
                    print(f"[billing] No invoice found for appointment {appointment_id}")
                    continue

                if status == "completed":
                    crud.update_invoice_status(db, invoice, InvoiceStatus.PAID)
                    print(f"[billing] Invoice {invoice.id} marked as paid")
                elif status in ("cancelled", "no_show"):
                    crud.update_invoice_status(db, invoice, InvoiceStatus.REFUNDED)
                    print(f"[billing] Invoice {invoice.id} marked as refunded")
            except Exception as e:
                print(f"[billing] Failed to update invoice status: {e}")
            finally:
                db.close()
