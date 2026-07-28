from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models


def get_availability_by_provider(db: Session, provider_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id
    ).all()


def get_availability_by_clinic(db: Session, provider_id: int, clinic_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id,
        models.ProviderAvailability.clinic_id == clinic_id,
    ).first()


#returns first row with conflict with supplied date
def get_availability_conflict(db: Session, provider_id: int, dates: list[str], exclude_clinic_id: int):
    other_rows = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id,
        models.ProviderAvailability.clinic_id != exclude_clinic_id,
    ).all()
    date_set = set(dates)
    for row in other_rows:
        for slot in (row.schedule or []):
            if slot.get("date") in date_set and slot.get("status") == "available":
                return row
    return None


def upsert_availability(db: Session, provider_id: int, clinic_id: int, schedule: list[dict]):
    existing = get_availability_by_clinic(db, provider_id, clinic_id)
    if existing:
        existing.schedule = schedule
        db.commit()
        db.refresh(existing)
        return existing
    db_avail = models.ProviderAvailability(
        provider_id=provider_id,
        clinic_id=clinic_id,
        schedule=schedule,
    )
    db.add(db_avail)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_avail)
    return db_avail


def setup_availability_schedule(
    db: Session, provider_id: int, clinic_id: int,
    working_days: list[str], start_time: str, end_time: str, days: int = 30
):
    today = date.today()
    schedule = []
    for i in range(days):
        d = today + timedelta(days=i)
        if d.strftime("%A") in working_days:
            schedule.append({
                "date": d.isoformat(),
                "start_time": start_time,
                "end_time": end_time,
                "status": "available",
            })
    return upsert_availability(db, provider_id, clinic_id, schedule)


def update_schedule_date_status(
    db: Session, avail: models.ProviderAvailability, target_date: str, status: str
):
    updated = False
    new_schedule = []
    for slot in (avail.schedule or []):
        if slot.get("date") == target_date:
            new_schedule.append({**slot, "status": status})
            updated = True
        else:
            new_schedule.append(slot)

    if not updated:
        return None  # date not found in schedule

    avail.schedule = new_schedule
    db.commit()
    db.refresh(avail)
    return avail


def delete_availability(db: Session, avail: models.ProviderAvailability):
    db.delete(avail)
    db.commit()
