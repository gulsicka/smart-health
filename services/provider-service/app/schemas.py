from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    class Config:
        from_attributes = True


class SpecialtyBase(BaseModel):
    name: str

class SpecialtyCreate(SpecialtyBase):
    pass

class Specialty(SpecialtyBase):
    id: int
    class Config:
        from_attributes = True


class ClinicBase(BaseModel):
    name: str
    address: str

class ClinicCreate(ClinicBase):
    pass

class Clinic(ClinicBase):
    id: int
    class Config:
        from_attributes = True


class ProviderBase(BaseModel):
    name: str
    email: EmailStr
    user_id: int
    department_id: Optional[int] = None

class ProviderCreate(ProviderBase):
    pass

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None

class Provider(ProviderBase):
    id: int
    class Config:
        from_attributes = True


class SlotBase(BaseModel):
    provider_id: int
    clinic_id: int
    start_time: datetime
    end_time: datetime

class SlotCreate(SlotBase):
    pass

class Slot(SlotBase):
    id: int
    is_available: bool
    class Config:
        from_attributes = True