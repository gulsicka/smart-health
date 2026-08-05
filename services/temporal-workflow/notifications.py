from celery import Celery
from config import settings

celery_app = Celery(broker=settings.RABBITMQ_URL)


def notify_user_created(user_id: int, roles: list):
    celery_app.send_task(
        "tasks.send_user_created",
        args=[user_id, roles],
    )


def notify_user_creation_failed(user_id: int):
    celery_app.send_task(
        "tasks.send_user_creation_failed",
        args=[user_id],
    )


def notify_user_role_updated(user_id: int, roles: list):
    celery_app.send_task(
        "tasks.send_user_role_updated",
        args=[user_id, roles],
    )


def notify_user_role_update_failed(user_id: int, roles: list):
    celery_app.send_task(
        "tasks.send_user_role_update_failed",
        args=[user_id, roles],
    )


def notify_booking_created(patient_id: int, provider_id: int, date: str, start_time: str, end_time: str):
    celery_app.send_task(
        "tasks.send_booking_created",
        args=[patient_id, provider_id, date, start_time, end_time],
    )


def notify_booking_failed(patient_id: int, provider_id: int, clinic_id: int, start_time: str, end_time: str):
    celery_app.send_task(
        "tasks.send_booking_failed",
        args=[patient_id, provider_id, clinic_id, start_time, end_time],
    )


def notify_appointment_reminder(patient_id: int, appointment_id: int, message: str):
    celery_app.send_task(
        "tasks.send_appointment_reminder_with_message",
        args=[patient_id, appointment_id, message],
    )
