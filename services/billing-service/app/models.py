from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, UniqueConstraint
from app.database import Base
from app.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, unique=True, nullable=False, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    provider_id = Column(Integer, nullable=False)
    clinic_id = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default=InvoiceStatus.PENDING, nullable=False)
    appointment_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
