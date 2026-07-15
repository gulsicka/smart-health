from celery_app import app
from database import SessionLocal
from models import Notification


@app.task
def send_booking_confirmation(user_id: int, appointment_id: int):
    print(f"[MOCK] Sending booking confirmation to user {user_id} for appointment {appointment_id}")
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=user_id,
            message=f"Your appointment {appointment_id} has been confirmed.",
            type="booking_confirmation",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()
        
@app.task
def send_appointment_reminder(user_id: int, appointment_id: int):
    print(f"[MOCK] Sending appointment reminder to user {user_id} for appointment {appointment_id}")
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=user_id,
            message=f"Reminder: You have an appointment {appointment_id} coming up.",
            type="appointment_reminder",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()
    
@app.task
def send_appointment_cancellation(user_id: int, appointment_id: int):
    print(f"[MOCK] Sending appointment cancellation to user {user_id} for appointment {appointment_id}")
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=user_id,
            message=f"Your appointment {appointment_id} has been cancelled.",
            type="appointment_cancellation",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()