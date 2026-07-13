from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models
from app.enums import AppointmentStatus


def create_appointment_internal(db: Session, appointment_data: dict):
    db_appointment = models.Appointment(**appointment_data)
    db.add(db_appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Slot already exists — return the existing record (idempotency)
        return db.query(models.Appointment).filter(
            models.Appointment.provider_id == appointment_data["provider_id"],
            models.Appointment.date == appointment_data["date"],
            models.Appointment.start_time == appointment_data["start_time"],
        ).first()
    db.refresh(db_appointment)
    return db_appointment


def get_all_appointments(db: Session):
    return db.query(models.Appointment).all()


def get_appointment_by_id(db: Session, appointment_id: int):
    return db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()


def update_appointment_status(db: Session, appointment: models.Appointment, new_status: AppointmentStatus):
    appointment.status = new_status
    db.commit()
    db.refresh(appointment)
    return appointment


def get_booked_slots(db: Session, provider_id: int, date: date, clinic_id: int):
    return db.query(models.Appointment).filter(
        models.Appointment.provider_id == provider_id,
        models.Appointment.date == date,
        models.Appointment.clinic_id == clinic_id,
        models.Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.FAILED]),
    ).all()


def delete_appointment(db: Session, appointment: models.Appointment):
    db.delete(appointment)
    db.commit()
