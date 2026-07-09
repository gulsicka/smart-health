from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, oauth
from app.enums import RoleName

router = APIRouter()

@router.post("/roles", response_model=schemas.Role)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))):
    existing = db.query(models.Role).filter(models.Role.role_name == role.role_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
    db_role = models.Role(**role.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    print(f"User {current_user.user_id} created role {db_role.role_name}")
    return db_role


@router.get("/roles", response_model=list[schemas.Role])
def get_roles(db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.get_current_user)):
    return db.query(models.Role).all()


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    print(f"User {current_user.user_id} deleted role {role.role_name}")
    return {"message": "Role deleted"}