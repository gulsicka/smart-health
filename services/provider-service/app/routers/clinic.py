from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, oauth, crud
from app.enums import RoleName

router = APIRouter()

R = RoleName


@router.post("/clinics", response_model=schemas.Clinic)
def create_clinic(
    clinic: schemas.ClinicCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN)),
):
    return crud.create_clinic(db, clinic.model_dump())


@router.get("/clinics", response_model=list[schemas.Clinic])
def get_clinics(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user),
):
    return crud.get_all_clinics(db)


@router.get("/clinics/{clinic_id}", response_model=schemas.Clinic)
def get_clinic(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user),
):
    clinic = crud.get_clinic_by_id(db, clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.post("/clinics/{clinic_id}/departments", response_model=schemas.Clinic)
def add_department_to_clinic(
    clinic_id: int,
    body: schemas.ClinicAddDepartment,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN)),
):
    clinic = crud.get_clinic_by_id(db, clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    dept = crud.get_department_by_id(db, body.department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept in clinic.departments:
        raise HTTPException(status_code=400, detail="Department already in this clinic")
    return crud.add_department_to_clinic(db, clinic, dept)


@router.delete("/clinics/{clinic_id}/departments/{department_id}", response_model=schemas.Clinic)
def remove_department_from_clinic(
    clinic_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN)),
):
    clinic = crud.get_clinic_by_id(db, clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    dept = crud.get_department_by_id(db, department_id)
    if not dept or dept not in clinic.departments:
        raise HTTPException(status_code=404, detail="Department not in this clinic")
    return crud.remove_department_from_clinic(db, clinic, dept)
