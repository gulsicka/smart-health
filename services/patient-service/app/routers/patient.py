from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, auth, crud, kafka_producer
from app.enums import RoleName

router = APIRouter()

R = RoleName


@router.post("/patients", tags=["Patients"], response_model=schemas.Patient)
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


@router.get("/patients", tags=["Patients"], response_model=list[schemas.Patient])
def get_patients(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF, R.PROVIDER)),
):
    return crud.get_all_patients(db)


@router.get("/patients/by-user-id/{user_id}", tags=["Patients"], response_model=schemas.Patient)
def get_patient_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    # a patient looks up their own profile (to learn their patient_id) from the
    # user_id in their token; admin, front-desk staff and providers may look up anyone's
    can_view_any = any(r in (R.ADMIN, R.FD_STAFF, R.PROVIDER) for r in current_user.roles)
    if current_user.user_id != user_id and not can_view_any:
        raise HTTPException(status_code=403, detail="You can only view your own patient profile")
    patient = crud.get_patient_by_user_id(db, user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/patients/{patient_id}", tags=["Patients"], response_model=schemas.Patient)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF, R.PROVIDER)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/patients/{patient_id}", tags=["Patients"], response_model=schemas.Patient)
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


@router.delete("/patients/{patient_id}", tags=["Patients"])
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF)),
):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    crud.soft_delete_patient(db, patient)
    await kafka_producer.publish_patient_deleted(patient.id, patient.user_id)
    return {"message": "Patient deleted"}


@router.delete("/patients/by-user-id/{user_id}", tags=["Patients"])
async def delete_patient_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.FD_STAFF)),
):
    patient = crud.soft_delete_patient_by_user_id(db, user_id)
    if patient:
        await kafka_producer.publish_patient_deleted(patient.id, user_id)
    return {"message": "Patient deleted"}
