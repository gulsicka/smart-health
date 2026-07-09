from pydantic import BaseModel
from app.enums import RoleName
from datetime import datetime
from typing import Optional


class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]



class PatientBase(BaseModel):
    date_of_birth: datetime
    user_id: int


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    date_of_birth: Optional[datetime] = None


class Patient(PatientBase):
    id: int

    class Config:
        from_attributes = True


