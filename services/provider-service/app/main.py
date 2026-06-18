from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app import models, schemas

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "service": "provider-service"}


@app.post("/departments", response_model=schemas.Department)
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Department).filter(models.Department.name == dept.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")
    db_dept = models.Department(**dept.model_dump())
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

@app.get("/departments", response_model=list[schemas.Department])
def get_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).all()

@app.post("/specialties", response_model=schemas.Specialty)
def create_specialty(spec: schemas.SpecialtyCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Specialty).filter(models.Specialty.name == spec.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Specialty already exists")
    db_spec = models.Specialty(**spec.model_dump())
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec


@app.get("/specialties", response_model=list[schemas.Specialty])
def get_specialties(db: Session = Depends(get_db)):
    return db.query(models.Specialty).all()

@app.post("/clinics", response_model=schemas.Clinic)
def create_clinic(clinic: schemas.ClinicCreate, db: Session = Depends(get_db)):
    db_clinic = models.Clinic(**clinic.model_dump())
    db.add(db_clinic)
    db.commit()
    db.refresh(db_clinic)
    return db_clinic


@app.get("/clinics", response_model=list[schemas.Clinic])
def get_clinics(db: Session = Depends(get_db)):
    return db.query(models.Clinic).all()

@app.post("/providers", response_model=schemas.Provider)
def create_provider(provider: schemas.ProviderCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Provider).filter(models.Provider.user_id == provider.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider already exists for this user")
    db_provider = models.Provider(**provider.model_dump())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


@app.get("/providers", response_model=list[schemas.Provider])
def get_providers(db: Session = Depends(get_db)):
    return db.query(models.Provider).all()


@app.get("/providers/{provider_id}", response_model=schemas.Provider)
def get_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@app.put("/providers/{provider_id}", response_model=schemas.Provider)
def update_provider(provider_id: int, updates: schemas.ProviderUpdate, db: Session = Depends(get_db)):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)
    db.commit()
    db.refresh(provider)
    return provider


@app.delete("/providers/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
    return {"message": "Provider deleted"}

@app.post("/slots", response_model=schemas.Slot)
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(get_db)):
    db_slot = models.Slot(**slot.model_dump())
    db.add(db_slot)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Slot already exists for this provider at this time")
    db.refresh(db_slot)
    return db_slot


@app.get("/providers/{provider_id}/slots", response_model=list[schemas.Slot])
def get_provider_slots(provider_id: int, db: Session = Depends(get_db)):
    return db.query(models.Slot).filter(models.Slot.provider_id == provider_id).all()