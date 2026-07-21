from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, Boolean
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    date_of_birth = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False, unique=True)
    is_deleted = Column(Boolean, nullable=False, default=False)