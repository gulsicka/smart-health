from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, oauth, crud
from app.enums import RoleName

router = APIRouter()


@router.post("/roles", response_model=schemas.Role)
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    if crud.get_role_by_name(db, role.role_name):
        raise HTTPException(status_code=400, detail="Role already exists")
    db_role = crud.create_role(db, role.role_name)
    print(f"User {current_user.user_id} created role {db_role.role_name}")
    return db_role


@router.get("/roles", response_model=list[schemas.Role])
def get_roles(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user),
):
    return crud.get_all_roles(db)


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    role = crud.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    print(f"User {current_user.user_id} deleted role {role.role_name}")
    crud.delete_role(db, role)
    return {"message": "Role deleted"}
