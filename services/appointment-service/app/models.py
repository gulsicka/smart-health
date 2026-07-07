from sqlalchemy import Column, Integer, String, DateTime, Date, Time
from datetime import datetime
from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False)      # cross-service ref, no FK
    provider_id = Column(Integer, nullable=False)     # cross-service ref, no FK
    clinic_id = Column(Integer, nullable=False)       # cross-service ref, no FK
    department_id = Column(Integer, nullable=False)   # cross-service ref, no FK
    date = Column(Date, nullable=False)               # e.g. 2026-07-10
    start_time = Column(Time, nullable=False)         # e.g. 14:00
    end_time = Column(Time, nullable=False)           # e.g. 14:30
    status = Column(String, nullable=False, default="requested")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
