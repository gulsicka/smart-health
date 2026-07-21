from sqlalchemy import Boolean, Column, Integer, String, Date, ForeignKey, Time, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Many-to-many junction: clinics ↔ departments
clinic_departments = Table(
    "clinic_departments",
    Base.metadata,
    Column("clinic_id", Integer, ForeignKey("clinics.id"), primary_key=True),
    Column("department_id", Integer, ForeignKey("departments.id"), primary_key=True),
)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    clinics = relationship("Clinic", secondary=clinic_departments, back_populates="departments")


class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    departments = relationship("Department", secondary=clinic_departments, back_populates="clinics")


class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    department = relationship("Department")
    availability = relationship("ProviderAvailability", back_populates="provider")


class ProviderAvailability(Base):
    __tablename__ = "provider_availability"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    date = Column(Date, nullable=False)   
    start_time = Column(Time, nullable=False)       # e.g. 12:00
    end_time = Column(Time, nullable=False)         # e.g. 18:00

    # A provider can only have one window per clinic per day
    __table_args__ = (
        UniqueConstraint("provider_id", "clinic_id", "date", name="uq_provider_clinic_day"),
    )

    provider = relationship("Provider", back_populates="availability")
    clinic = relationship("Clinic")
