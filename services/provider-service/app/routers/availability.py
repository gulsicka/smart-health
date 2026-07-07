from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app import models, schemas, oauth

router = APIRouter()


@router.post("/providers/{provider_id}/availability", response_model=schemas.ProviderAvailability)
def set_availability(
    provider_id: int,
    avail: schemas.ProviderAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role("admin"))
):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    clinic = db.query(models.Clinic).filter(models.Clinic.id == avail.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    # Ensure the provider's department is offered at this clinic
    dept_in_clinic = any(d.id == provider.department_id for d in clinic.departments)
    if not dept_in_clinic:
        raise HTTPException(
            status_code=400,
            detail="Provider's department is not available at this clinic"
        )

    # Ensure provider isn't already assigned to another clinic on the same day
    conflict = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id,
        models.ProviderAvailability.day_of_week == avail.day_of_week,
        models.ProviderAvailability.clinic_id != avail.clinic_id,
    ).first()
    if conflict:
        raise HTTPException(
            status_code=400,
            detail=f"Provider already has availability at a different clinic on {avail.day_of_week}"
        )

    db_avail = models.ProviderAvailability(
        provider_id=provider_id,
        clinic_id=avail.clinic_id,
        day_of_week=avail.day_of_week,
        start_time=avail.start_time,
        end_time=avail.end_time,
    )
    db.add(db_avail)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Availability already set for this provider at this clinic on this day"
        )
    db.refresh(db_avail)
    return db_avail


@router.get("/providers/{provider_id}/availability", response_model=list[schemas.ProviderAvailability])
def get_availability(provider_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    return db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.provider_id == provider_id
    ).all()


@router.delete("/providers/{provider_id}/availability/{availability_id}")
def delete_availability(provider_id: int, availability_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin"))):
    avail = db.query(models.ProviderAvailability).filter(
        models.ProviderAvailability.id == availability_id,
        models.ProviderAvailability.provider_id == provider_id,
    ).first()
    if not avail:
        raise HTTPException(status_code=404, detail="Availability not found")
    db.delete(avail)
    db.commit()
    return {"message": "Availability deleted"}
