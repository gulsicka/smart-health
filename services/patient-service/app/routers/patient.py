from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, auth, crud, kafka_producer
from app.enums import RoleName

router = APIRouter()

R = RoleName


@router.post("/patients", response_model=schemas.Patient)
async def create_patient(
    patient: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF)),
):
    if crud.get_patient_by_user_id(db, patient.user_id):
        raise HTTPException(status_code=400, detail="Patient profile already exists for this user")
    db_patient = crud.create_patient(db, patient)
    await kafka_producer.publish_event(
        event={"event_type": "patient.created", "patient_id": db_patient.id, "user_id": db_patient.user_id},
        key=str(db_patient.id),
    )
    return db_patient


@router.get("/patients", response_model=list[schemas.Patient])
def get_patients(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF, R.PROVIDER)),
):
    return crud.get_all_patients(db)


@router.get("/patients/{patient_id}", response_model=schemas.Patient)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF, R.PROVIDER)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/patients/{patient_id}", response_model=schemas.Patient)
def update_patient(
    patient_id: int,
    updates: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return crud.update_patient(db, patient, updates)


@router.delete("/patients/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    crud.soft_delete_patient(db, patient)
    await kafka_producer.publish_patient_deleted(patient.id, patient.user_id)
    return {"message": "Patient deleted"}


@router.delete("/patients/by-user-id/{user_id}")
async def delete_patient_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    patient = crud.soft_delete_patient_by_user_id(db, user_id)
    if patient:
        await kafka_producer.publish_patient_deleted(patient.id, user_id)
    return {"message": "Patient deleted"}
