from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TokenData(BaseModel):
    user_id: int
    roles: list[str]



class PatientBase(BaseModel):
    date_of_birth: datetime


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    date_of_birth: Optional[datetime] = None


class Patient(PatientBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


