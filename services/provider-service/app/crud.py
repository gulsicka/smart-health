from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models


# ── Departments ──────────────────────────────────────────────────────────────

def get_department_by_id(db: Session, department_id: int):
    return db.query(models.Department).filter(models.Department.id == department_id).first()


def get_department_by_name(db: Session, name: str):
    return db.query(models.Department).filter(models.Department.name == name).first()


def get_all_departments(db: Session):
    return db.query(models.Department).all()


def create_department(db: Session, name: str, description: str | None = None):
    db_dept = models.Department(name=name, description=description)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept


# ── Clinics ───────────────────────────────────────────────────────────────────

def get_clinic_by_id(db: Session, clinic_id: int):
    return db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()


def get_all_clinics(db: Session):
    return db.query(models.Clinic).all()


def create_clinic(db: Session, clinic_data: dict):
    db_clinic = models.Clinic(**clinic_data)
    db.add(db_clinic)
    db.commit()
    db.refresh(db_clinic)
    return db_clinic


def add_department_to_clinic(db: Session, clinic: models.Clinic, dept: models.Department):
    clinic.departments.append(dept)
    db.commit()
    db.refresh(clinic)
    return clinic


def remove_department_from_clinic(db: Session, clinic: models.Clinic, dept: models.Department):
    clinic.departments.remove(dept)
    db.commit()
    db.refresh(clinic)
    return clinic


# ── Providers ─────────────────────────────────────────────────────────────────

def get_provider_by_id(db: Session, provider_id: int):
    return db.query(models.Provider).filter(models.Provider.id == provider_id).first()


def get_provider_by_user_id(db: Session, user_id: int):
    return db.query(models.Provider).filter(models.Provider.user_id == user_id).first()


def get_providers(db: Session, clinic_id: int | None = None, department_id: int | None = None):
    query = db.query(models.Provider)
    if clinic_id is not None:
        query = (
            query.join(models.ProviderAvailability, models.Provider.id == models.ProviderAvailability.provider_id)
            .filter(models.ProviderAvailability.clinic_id == clinic_id)
            .distinct()
        )
    if department_id is not None:
        query = query.filter(models.Provider.department_id == department_id)
    return query.all()


def create_provider(db: Session, provider_data: dict):
    db_provider = models.Provider(**provider_data)
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


def delete_provider(db: Session, provider: models.Provider):
    db.delete(provider)
    db.commit()


# ── Availability ──────────────────────────────────────────────────────────────

def get_availability_by_provider(db: Session, provider_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id
    ).all()


def get_availability_conflict(db: Session, provider_id: int, date, exclude_clinic_id: int):
    """Check if the provider already has availability at a different clinic on the same date."""
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


def get_availability_by_id(db: Session, provider_id: int, availability_id: int):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.id == availability_id,
        models.ProviderAvailability.provider_id == provider_id,
    ).first()
