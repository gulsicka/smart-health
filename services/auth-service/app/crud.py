from sqlalchemy.orm import Session
from app import models, utils


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_all_users(db: Session):
    return db.query(models.User).all()


def get_roles_by_ids(db: Session, role_ids: list[int]):
    return db.query(models.Role).filter(models.Role.id.in_(role_ids)).all()


def create_user(db: Session, name: str, email: str, number: str, password: str, roles: list):
    db_user = models.User(
        name=name,
        email=email,
        number=number,
        password_hash=utils.hash_password(password),
        roles=roles,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: models.User, name: str | None, email: str | None, number: str | None, roles: list | None):
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    if number is not None:
        user.number = number
    if roles is not None:
        user.roles = roles
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: models.User):
    db.delete(user)
    db.commit()


def activate_user(db: Session, user: models.User):
    from app.enums import UserStatus
    user.status = UserStatus.ACTIVE
    db.commit()


def get_all_roles(db: Session):
    return db.query(models.Role).all()


def get_role_by_id(db: Session, role_id: int):
    return db.query(models.Role).filter(models.Role.id == role_id).first()


def get_role_by_name(db: Session, role_name: str):
    return db.query(models.Role).filter(models.Role.role_name == role_name).first()


def create_role(db: Session, role_name: str):
    db_role = models.Role(role_name=role_name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, role: models.Role):
    db.delete(role)
    db.commit()
