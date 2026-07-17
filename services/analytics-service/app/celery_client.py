from celery import Celery
from .config import settings

celery_app = Celery("analytics_service", broker=settings.RABBITMQ_URL)


def notify_booking_confirmation(patient_id: int, appointment_id: int):
    celery_app.send_task("tasks.send_booking_confirmation", args=[patient_id, appointment_id])


def notify_appointment_cancellation(patient_id: int, appointment_id: int):
    celery_app.send_task("tasks.send_appointment_cancellation", args=[patient_id, appointment_id])
