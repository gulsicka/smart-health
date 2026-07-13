from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, oauth, crud
from app.enums import RoleName

router = APIRouter()

R = RoleName


@router.post("/patients", response_model=schemas.Patient)
def create_patient(
    patient: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN, R.FD_STAFF)),
):
    if crud.get_patient_by_user_id(db, patient.user_id):
        raise HTTPException(status_code=400, detail="Patient profile already exists for this user")
    return crud.create_patient(db, patient.model_dump())


@router.get("/patients", response_model=list[schemas.Patient])
def get_patients(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN, R.FD_STAFF, R.PROVIDER)),
):
    return crud.get_all_patients(db)


@router.get("/patients/{patient_id}", response_model=schemas.Patient)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN, R.FD_STAFF, R.PROVIDER)),
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
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN, R.FD_STAFF)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return crud.update_patient(db, patient, updates.model_dump(exclude_unset=True))


@router.delete("/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    crud.delete_patient(db, patient)
    return {"message": "Patient deleted"}


@router.delete("/patients/by-user-id/{user_id}")
def delete_patient_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN)),
):
    crud.delete_patient_by_user_id(db, user_id)
    return {"message": "Patient deleted"}  # idempotent - 200 even if not found
