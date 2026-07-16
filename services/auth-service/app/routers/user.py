from datetime import timedelta
from uuid import uuid4
from fastapi.security import HTTPAuthorizationCredentials

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, utils, auth, crud, tasks
from app.utils import workflow_id_for, workflow_id_for_update
from app.enums import RoleName, UserStatus
from app.config import settings
from app.redis import get_redis

router = APIRouter()


@router.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF)),
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
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    return crud.get_all_users(db)


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    updates: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_roles = [r.id for r in user.roles] if user.roles else []
    new_roles = [role_id for role_id in updates.role_ids if role_id not in old_roles] if updates.role_ids else []
    print(f"old_roles: {old_roles}")
    print(f"new_roles: {new_roles}")

    roles = None
    if updates.role_ids is not None:
        roles = crud.get_roles_by_ids(db, updates.role_ids)
        if len(roles) != len(updates.role_ids):
            raise HTTPException(status_code=404, detail="One or more roles not found")
    
    updated_user =  crud.update_user(db, user, updates.name, updates.email, updates.number, roles)

    # starting workflow for creation of patient/provider according to role for existing user
    new_role_names = [r.role_name for r in user.roles if r.id in new_roles] if new_roles else []
    print(f"new_role_names: {new_role_names}")
    if "patient" in new_role_names or "provider" in new_role_names:
        handle = await tasks.start_update_user_role_workflow(
            user_data={
                "id": user.id,
                "roles": new_role_names,
                "date_of_birth": updates.date_of_birth.isoformat() if updates.date_of_birth else None
            },
            workflow_id=workflow_id_for_update(user.id),
        )
        print(f"Update user role workflow started! ID: {handle.id}")

    return updated_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, user)
    return {"message": "User deleted"}


@router.post("/login")
def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, credentials.email)
    if not user or not utils.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=403, detail="Account setup is still in progress")

    access_token = auth.create_access_token(data={
        "user_id": user.id,
        "roles": [r.role_name for r in user.roles],
    })
    print(f"User {user.id} logged in")
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(auth.bearer_scheme),
    redis = Depends(get_redis),
):
    jti = auth.get_jti_from_token(credentials)
    await redis.setex(f"blacklist:{jti}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "true") # individual token keys, with an expiry time. a list here would require going thru each itema nd checking if the token is in the list is expired or not, which is less efficient than just checking if the key exists.
    return {"message": "Logout successful"}


@router.patch("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.activate_user(db, user)
    return {"message": "User activated"}

@router.patch("/users/{user_id}/remove_roles")
def remove_user_role(
    user_id: int,
    data: schemas.RemoveRolesRequest,
    db: Session = Depends(get_db),  
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.remove_user_roles(db, user, data.role_names)
    return {"message": "Role removed from user"}
