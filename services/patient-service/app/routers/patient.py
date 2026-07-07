from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, oauth

router = APIRouter()


@router.post("/patients", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin", "fd_staff"))):
    existing = db.query(models.Patient).filter(models.Patient.user_id == patient.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient profile already exists for this user")
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("/patients", response_model=list[schemas.Patient])
def get_patients(db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin", "fd_staff", "provider"))):
    return db.query(models.Patient).all()


@router.get("/patients/{patient_id}", response_model=schemas.Patient)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin", "fd_staff", "provider"))):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/patients/{patient_id}", response_model=schemas.Patient)
def update_patient(patient_id: int, updates: schemas.PatientUpdate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin", "fd_staff"))):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin"))):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted"}
