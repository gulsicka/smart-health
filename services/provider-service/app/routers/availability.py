from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app import schemas, auth, crud
from app.enums import RoleName

router = APIRouter()

R = RoleName


@router.post("/providers/{provider_id}/availability", response_model=schemas.ProviderAvailability)
def set_availability(
    provider_id: int,
    avail: schemas.ProviderAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    provider = crud.get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    clinic = crud.get_clinic_by_id(db, avail.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    if not any(d.id == provider.department_id for d in clinic.departments):
        raise HTTPException(status_code=400, detail="Provider's department is not available at this clinic")

    incoming_dates = [s.date for s in avail.schedule]
    if crud.get_availability_conflict(db, provider_id, incoming_dates, exclude_clinic_id=avail.clinic_id):
        raise HTTPException(status_code=400, detail="Provider already has availability at a different clinic on one or more of these dates")

    try:
        return crud.upsert_availability(db, provider_id, avail.clinic_id, [s.dict() for s in avail.schedule])
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Could not save availability")


@router.post("/providers/{provider_id}/setup-availability", response_model=schemas.ProviderAvailability)
def setup_availability(
    provider_id: int,
    setup: schemas.ProviderAvailabilitySetup,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    provider = crud.get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    clinic = crud.get_clinic_by_id(db, setup.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    if not any(d.id == provider.department_id for d in clinic.departments):
        raise HTTPException(status_code=400, detail="Provider's department is not available at this clinic")

    try:
        return crud.setup_availability_schedule(
            db,
            provider_id=provider_id,
            clinic_id=setup.clinic_id,
            working_days=setup.working_days,
            start_time=setup.start_time,
            end_time=setup.end_time,
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Could not save availability schedule")


@router.get("/providers/{provider_id}/availability", response_model=list[schemas.ProviderAvailability])
def get_availability(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    return crud.get_availability_by_provider(db, provider_id)


@router.patch("/providers/{provider_id}/availability/{clinic_id}/date-status", response_model=schemas.ProviderAvailability)
def update_date_status(
    provider_id: int,
    clinic_id: int,
    body: schemas.ScheduleDateStatusUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN, R.PROVIDER)),
):
    avail = crud.get_availability_by_clinic(db, provider_id, clinic_id)
    if not avail:
        raise HTTPException(status_code=404, detail="Availability not found")

    updated = crud.update_schedule_date_status(db, avail, body.date, body.status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Date {body.date} not found in schedule")

    return updated


@router.delete("/providers/{provider_id}/availability/{clinic_id}")
def delete_availability(
    provider_id: int,
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    avail = crud.get_availability_by_clinic(db, provider_id, clinic_id)
    if not avail:
        raise HTTPException(status_code=404, detail="Availability not found")
    crud.delete_availability(db, avail)
    return {"message": "Availability deleted"}
