from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, oauth

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "service": "patient-service"}


@app.post("/patients", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    existing = db.query(models.Patient).filter(models.Patient.email == patient.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_patient = models.Patient(**patient.model_dump(), user_id=current_user.user_id)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@app.get("/patients", response_model=list[schemas.Patient])
def get_patients(db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    return db.query(models.Patient).all()


@app.get("/patients/{patient_id}", response_model=schemas.Patient)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.put("/patients/{patient_id}", response_model=schemas.Patient)
def update_patient(patient_id: int, updates: schemas.PatientUpdate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted"}