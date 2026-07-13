from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, utils, oauth, crud, tasks
from app.utils import workflow_id_for
from app.enums import RoleName, UserStatus

router = APIRouter()


@router.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN, RoleName.FD_STAFF)),
):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    roles = crud.get_roles_by_ids(db, user.role_ids)
    if len(roles) != len(user.role_ids):
        raise HTTPException(status_code=404, detail="One or more roles not found")

    db_user = crud.create_user(
        db,
        name=user.name,
        email=user.email,
        number=user.number,
        password=user.password,
        roles=roles,
    )

    workflow_id = workflow_id_for(db_user.id)
    handle = await tasks.start_user_creation_workflow(
        user_data={
            "id": db_user.id,
            "roles": [r.role_name for r in db_user.roles],
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "department_id": user.department_id,
        },
        workflow_id=workflow_id,
    )
    print(f"Workflow started! ID: {handle.id}")
    print(f"User {current_user.user_id} created user {db_user.email}")
    return db_user


@router.get("/users", response_model=list[schemas.User])
def get_users(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    return crud.get_all_users(db)


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    updates: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = None
    if updates.role_ids is not None:
        roles = crud.get_roles_by_ids(db, updates.role_ids)
        if len(roles) != len(updates.role_ids):
            raise HTTPException(status_code=404, detail="One or more roles not found")

    return crud.update_user(db, user, updates.name, updates.email, updates.number, roles)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, user)
    return {"message": "User deleted"}


@router.post("/login")
def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, credentials.username)
    if not user or not utils.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=403, detail="Account setup is still in progress")

    access_token = oauth.create_access_token(data={
        "user_id": user.id,
        "roles": [r.role_name for r in user.roles],
    })
    print(f"User {user.id} logged in")
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}


@router.patch("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.activate_user(db, user)
    return {"message": "User activated"}
