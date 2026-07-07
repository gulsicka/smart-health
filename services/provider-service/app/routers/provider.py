from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/providers", response_model=schemas.Provider)
def create_provider(provider: schemas.ProviderCreate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin"))):
    # Validate department exists
    department = db.query(models.Department).filter(models.Department.id == provider.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    existing = db.query(models.Provider).filter(models.Provider.user_id == provider.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider already exists for this user")

    db_provider = models.Provider(**provider.model_dump())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


@router.get("/providers", response_model=list[schemas.Provider])
def get_providers(
    clinic_id: Optional[int] = Query(None, description="Filter providers who have availability at this clinic"),
    department_id: Optional[int] = Query(None, description="Filter providers by department"),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user)
):
    query = db.query(models.Provider)

    if clinic_id is not None:
        # Return providers who have at least one availability slot at this clinic
        query = query.join(
            models.ProviderAvailability,
            models.Provider.id == models.ProviderAvailability.provider_id
        ).filter(
            models.ProviderAvailability.clinic_id == clinic_id
        ).distinct()

    if department_id is not None:
        query = query.filter(models.Provider.department_id == department_id)

    return query.all()


@router.get("/providers/{provider_id}", response_model=schemas.Provider)
def get_provider(provider_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.delete("/providers/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin"))):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
    return {"message": "Provider deleted"}
