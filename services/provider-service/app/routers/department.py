from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, oauth, crud
from app.enums import RoleName

router = APIRouter()

R = RoleName


@router.post("/departments", response_model=schemas.Department)
def create_department(
    dept: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(R.ADMIN)),
):
    if crud.get_department_by_name(db, dept.name):
        raise HTTPException(status_code=400, detail="Department already exists")
    return crud.create_department(db, name=dept.name, description=getattr(dept, "description", None))


@router.get("/departments", response_model=list[schemas.Department])
def get_departments(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user),
):
    return crud.get_all_departments(db)


@router.get("/departments/{department_id}", response_model=schemas.Department)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user),
):
    department = crud.get_department_by_id(db, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department
