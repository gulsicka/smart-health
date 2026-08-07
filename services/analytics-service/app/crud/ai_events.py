from app.database import SessionLocal
from app.models import AIInteractionEvent
from datetime import datetime


def insert_ai_event(event: dict, event_type: str):
    db = SessionLocal()
    try:
        db.add(AIInteractionEvent(
            time=datetime.utcnow(),
            event_type=event_type,
            status=event.get("status") or "unknown",
            communication_type=event.get("communication_type"),
            user_id=event.get("user_id"),
        ))
        db.commit()
    finally:
        db.close()
