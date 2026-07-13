from sqlalchemy.orm import Session
from app import models


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
