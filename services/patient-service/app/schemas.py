from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class PatientBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    number: str
    date_of_birth: datetime


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    number: Optional[str] = None
    date_of_birth: Optional[datetime] = None


class Patient(PatientBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class AuditLogBase(BaseModel):
    entity_id: int
    action: str
    changed_by: int


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None