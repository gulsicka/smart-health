from celery_app import app
from database import SessionLocal
from models import Notification


@app.task
def send_user_created(user_id: int, roles: list):
    print(f"[MOCK] Sending user created notification to user {user_id}")
    db = SessionLocal()
    try:
        roles_str = ", ".join(roles)
        notification = Notification(
            user_id=user_id,
            message=f"Your account (ID: {user_id}) has been successfully created with role(s): {roles_str}.",
            type="user_created",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


@app.task
def send_user_creation_failed(user_id: int):
    print(f"[MOCK] Sending user creation failed notification for user {user_id}")
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=user_id,
            message=f"Account creation for user ID {user_id} failed. Please try again.",
            type="user_creation_failed",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


@app.task
def send_user_role_updated(user_id: int, roles: list):
    db = SessionLocal()
    try:
        roles_str = ", ".join(roles)
        notification = Notification(
            user_id=user_id,
            message=f"Your account has been updated with new role(s): {roles_str}.",
            type="user_role_updated",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


@app.task
def send_user_role_update_failed(user_id: int, roles: list):
    db = SessionLocal()
    try:
        roles_str = ", ".join(roles)
        notification = Notification(
            user_id=user_id,
            message=f"Role update failed for role(s): {roles_str}. The changes have been rolled back.",
            type="user_role_update_failed",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


@app.task
def send_booking_created(patient_id: int, provider_id: int, date: str, start_time: str, end_time: str):
    print(f"[MOCK] Sending booking created notification to patient {patient_id}")
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=patient_id,
            message=f"Your appointment with provider {provider_id} on {date} from {start_time} to {end_time} has been successfully booked.",
            type="booking_created",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()


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


@app.task
def send_booking_failed(patient_id: int, provider_id: int, clinic_id: int, start_time: str, end_time: str):
    print(f"[MOCK] Sending booking failed notification to patient {patient_id}")
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=patient_id,
            message=f"Your appointment booking at clinic {clinic_id} with provider {provider_id} from {start_time} to {end_time} could not be confirmed. Please try again.",
            type="booking_failed",
        )
        db.add(notification)
        db.commit()
    finally:
        db.close()