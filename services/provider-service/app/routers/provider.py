from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.database import get_db
from app import schemas, auth, crud, kafka_producer
from app.enums import RoleName

router = APIRouter()


@router.post("/providers", response_model=schemas.Provider)
def create_provider(
    provider: schemas.ProviderCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    if not crud.get_department_by_id(db, provider.department_id):
        raise HTTPException(status_code=404, detail="Department not found")
    if crud.get_provider_by_user_id(db, provider.user_id):
        raise HTTPException(status_code=400, detail="Provider already exists for this user")
    return crud.create_provider(db, provider)


@router.get("/providers", response_model=list[schemas.Provider])
def get_providers(
    clinic_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    return crud.get_providers(db, clinic_id=clinic_id, department_id=department_id)


@router.get("/providers/by-user-id/{user_id}", response_model=schemas.Provider)
def get_provider_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    provider = crud.get_provider_by_user_id(db, user_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.get("/providers/{provider_id}", response_model=schemas.Provider)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    provider = crud.get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.delete("/providers/by-user-id/{user_id}")
async def delete_provider_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    provider = crud.soft_delete_provider_by_user_id(db, user_id)
    if provider:
        await kafka_producer.publish_provider_deleted(provider.id, user_id)
    return {"message": "Provider deleted"}


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    provider = crud.get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    crud.soft_delete_provider(db, provider)
    await kafka_producer.publish_provider_deleted(provider.id, provider.user_id)
    return {"message": "Provider deleted"}


@router.post("/providers/{provider_id}/setup-availability", status_code=201)
def setup_provider_availability(
    provider_id: int,
    body: schemas.ProviderAvailabilitySetup,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    if not crud.get_provider_by_id(db, provider_id):
        raise HTTPException(status_code=404, detail="Provider not found")
    if not crud.get_clinic_by_id(db, body.clinic_id):
        raise HTTPException(status_code=404, detail="Clinic not found")
    try:
        crud.setup_availability_schedule(
            db,
            provider_id=provider_id,
            clinic_id=body.clinic_id,
            working_days=body.working_days,
            start_time=body.start_time,
            end_time=body.end_time,
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Some availability slots already exist for this provider")
    return {"message": "Provider availability set up for the next 30 days"}
