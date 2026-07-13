from sqlalchemy.orm import Session
from app import models


def get_patient_by_user_id(db: Session, user_id: int):
    return db.query(models.Patient).filter(models.Patient.user_id == user_id).first()


def get_patient_by_id(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()


def get_all_patients(db: Session):
    return db.query(models.Patient).all()


def create_patient(db: Session, patient_data: dict):
    db_patient = models.Patient(**patient_data)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def update_patient(db: Session, patient: models.Patient, updates: dict):
    for field, value in updates.items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient: models.Patient):
    db.delete(patient)
    db.commit()


def delete_patient_by_user_id(db: Session, user_id: int):
    patient = get_patient_by_user_id(db, user_id)
    if patient:
        db.delete(patient)
        db.commit()
    return patient
