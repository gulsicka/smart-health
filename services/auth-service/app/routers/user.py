import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, utils, oauth
from app.utils import workflow_id_for
from app.enums import RoleName
from temporalio.client import Client

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TASK_QUEUE = os.getenv("USER_TASK_QUEUE")

router = APIRouter()


@router.post("/users", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN, RoleName.FD_STAFF))):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    roles = db.query(models.Role).filter(models.Role.id.in_(user.role_ids)).all()
    if len(roles) != len(user.role_ids):
        raise HTTPException(status_code=404, detail="One or more roles not found")

    db_user = models.User(
        name=user.name,
        email=user.email,
        number=user.number,
        password_hash=utils.hash_password(user.password),
        roles=roles,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    client = await Client.connect(TEMPORAL_HOST)

    workflow_id = workflow_id_for(db_user.id)

    handle = await client.start_workflow(
        "UserCreationWorkflow",
        {
        "id": db_user.id,
        "roles": [r.role_name for r in db_user.roles],
        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "department_id": user.department_id,
    },
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Workflow started! ID: {handle.id}")

   # await handle.result() (dont make user wait)

    print(f"User {current_user.user_id} created user {db_user.email}")
    return db_user


@router.get("/users", response_model=list[schemas.User])
def get_users(db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))):
    return db.query(models.User).all()


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, updates: schemas.UserUpdate, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if updates.name is not None:
        user.name = updates.name
    if updates.email is not None:
        user.email = updates.email
    if updates.number is not None:
        user.number = updates.number
    if updates.role_ids is not None:
        roles = db.query(models.Role).filter(models.Role.id.in_(updates.role_ids)).all()
        if len(roles) != len(updates.role_ids):
            raise HTTPException(status_code=404, detail="One or more roles not found")
        user.roles = roles

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@router.post("/login")
def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.username).first()
    if not user or not utils.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")

    access_token = oauth.create_access_token(data={
        "user_id": user.id,
        "roles": [r.role_name for r in user.roles],
    })
    print(f"User {user.id} logged in")
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}
