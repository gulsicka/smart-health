from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String)
    number = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False, unique=True) # for the auth table id
    
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True,index=True)
    entity_id = Column(Integer,nullable=False)
    action = Column(String,nullable=False)
    timestamp = Column(DateTime,nullable=False, default=datetime.utcnow)
    changed_by = Column(Integer,nullable=False)