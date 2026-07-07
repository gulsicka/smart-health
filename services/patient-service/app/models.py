from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    date_of_birth = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False, unique=True)