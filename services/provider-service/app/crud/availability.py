from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models


def get_availability_by_provider(db: Session, provider_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id
    ).all()


def get_availability_by_id(db: Session, provider_id: int, availability_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.id == availability_id,
        models.ProviderAvailability.provider_id == provider_id,
    ).first()


def get_availability_conflict(db: Session, provider_id: int, date, exclude_clinic_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id,
        models.ProviderAvailability.date == date,
        models.ProviderAvailability.clinic_id != exclude_clinic_id,
    ).first()


def create_availability(db: Session, provider_id: int, clinic_id: int, date, start_time, end_time):
    db_avail = models.ProviderAvailability(
        provider_id=provider_id,
        clinic_id=clinic_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(db_avail)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_avail)
    return db_avail


def delete_availability(db: Session, avail: models.ProviderAvailability):
    db.delete(avail)
    db.commit()


def setup_availability_schedule(
    db: Session, provider_id: int, clinic_id: int,
    working_days: list[str], start_time: str, end_time: str, days: int = 30
):
    today = date.today()
    for i in range(days):
        d = today + timedelta(days=i)
        if d.strftime("%A") in working_days:
            db_avail = models.ProviderAvailability(
                provider_id=provider_id,
                clinic_id=clinic_id,
                date=d,
                start_time=start_time,
                end_time=end_time,
            )
            db.add(db_avail)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
