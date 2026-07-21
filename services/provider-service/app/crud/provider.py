from sqlalchemy.orm import Session
from app import models, schemas


def get_provider_by_id(db: Session, provider_id: int):
    return db.query(models.Provider).filter(models.Provider.id == provider_id).first()


def get_provider_by_user_id(db: Session, user_id: int):
    return db.query(models.Provider).filter(models.Provider.user_id == user_id).first()


def get_providers(db: Session, clinic_id: int | None = None, department_id: int | None = None):
    query = db.query(models.Provider)
    if clinic_id is not None:
        query = (
            query.join(models.ProviderAvailability, models.Provider.id == models.ProviderAvailability.provider_id)
            .filter(models.ProviderAvailability.clinic_id == clinic_id)
            .distinct()
        )
    if department_id is not None:
        query = query.filter(models.Provider.department_id == department_id)
    return query.all()


def create_provider(db: Session, provider_data: schemas.ProviderCreate):
    db_provider = models.Provider(**provider_data.model_dump())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


def delete_provider(db: Session, provider: models.Provider):
    db.delete(provider)
    db.commit()


def delete_provider_by_user_id(db: Session, user_id: int):
    provider = get_provider_by_user_id(db, user_id)
    if provider:
        db.delete(provider)
        db.commit()


def soft_delete_provider(db: Session, provider: models.Provider):
    provider.is_deleted = True
    db.commit()
    db.refresh(provider)
    return provider


def soft_delete_provider_by_user_id(db: Session, user_id: int):
    provider = get_provider_by_user_id(db, user_id)
    if provider:
        return soft_delete_provider(db, provider)
    return None
