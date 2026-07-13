from sqlalchemy.orm import Session
from app import models


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
