from sqlalchemy.orm import Session
from app import models


def get_department_by_id(db: Session, department_id: int):
    return db.query(models.Department).filter(models.Department.id == department_id).first()


def get_department_by_name(db: Session, name: str):
    return db.query(models.Department).filter(models.Department.name == name).first()


def get_all_departments(db: Session):
    return db.query(models.Department).all()


def create_department(db: Session, name: str, description: str | None = None):
    db_dept = models.Department(name=name, description=description)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept
