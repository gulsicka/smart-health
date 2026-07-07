from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, oauth

router = APIRouter()


@router.post("/clinics", response_model=schemas.Clinic)
def create_clinic(clinic: schemas.ClinicCreate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role("admin"))):
    db_clinic = models.Clinic(**clinic.model_dump())
    db.add(db_clinic)
    db.commit()
    db.refresh(db_clinic)
    return db_clinic


@router.get("/clinics", response_model=list[schemas.Clinic])
def get_clinics(db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    return db.query(models.Clinic).all()


@router.get("/clinics/{clinic_id}", response_model=schemas.Clinic)
def get_clinic(clinic_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.post("/clinics/{clinic_id}/departments", response_model=schemas.Clinic)
def add_department_to_clinic(
    clinic_id: int,
    body: schemas.ClinicAddDepartment,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role("admin"))
):
    clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    dept = db.query(models.Department).filter(models.Department.id == body.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept in clinic.departments:
        raise HTTPException(status_code=400, detail="Department already in this clinic")
    clinic.departments.append(dept)
    db.commit()
    db.refresh(clinic)
    return clinic


@router.delete("/clinics/{clinic_id}/departments/{department_id}", response_model=schemas.Clinic)
def remove_department_from_clinic(
    clinic_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role("admin"))
):
    clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    dept = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not dept or dept not in clinic.departments:
        raise HTTPException(status_code=404, detail="Department not in this clinic")
    clinic.departments.remove(dept)
    db.commit()
    db.refresh(clinic)
    return clinic
