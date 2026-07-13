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

    if crud.get_availability_conflict(db, provider_id, avail.date, exclude_clinic_id=avail.clinic_id):
        raise HTTPException(status_code=400, detail=f"Provider already has availability at a different clinic on {avail.date}")

    try:
        return crud.create_availability(db, provider_id, avail.clinic_id, avail.date, avail.start_time, avail.end_time)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Availability already set for this provider at this clinic on this day")


@router.get("/providers/{provider_id}/availability", response_model=list[schemas.ProviderAvailability])
def get_availability(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    return crud.get_availability_by_provider(db, provider_id)


@router.delete("/providers/{provider_id}/availability/{availability_id}")
def delete_availability(
    provider_id: int,
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    avail = crud.get_availability_by_id(db, provider_id, availability_id)
    if not avail:
        raise HTTPException(status_code=404, detail="Availability not found")
    crud.delete_availability(db, avail)
    return {"message": "Availability deleted"}
