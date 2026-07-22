from app.database import SessionLocal
from app.models import AppointmentEvent
from datetime import datetime


def insert_event(event: dict, event_type: str):
    db = SessionLocal()
    try:
        db.add(AppointmentEvent(
            time=datetime.utcnow(),
            event_type=event_type,
            clinic_id=event.get("clinic_id") or 0,
            provider_id=event.get("provider_id") or 0,
            patient_id=event.get("patient_id") or 0,
        ))
        db.commit()
    finally:
        db.close()