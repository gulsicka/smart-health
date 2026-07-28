from pydantic import BaseModel, validator
from app.enums import RoleName
from datetime import datetime
from typing import Optional

class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
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
    departments: list[Department] = []
    class Config:
        from_attributes = True


class ClinicAddDepartment(BaseModel):
    department_id: int


class ProviderBase(BaseModel):
    user_id: int
    department_id: int

class ProviderCreate(ProviderBase):
    pass

class ProviderUpdate(BaseModel):
    department_id: Optional[int] = None

class Provider(ProviderBase):
    id: int
    is_deleted: bool
    class Config:
        from_attributes = True


class ScheduleDay(BaseModel):
    date: str       
    start_time: str 
    end_time: str  
    status: str = "available" 


class ProviderAvailabilityCreate(BaseModel):
    clinic_id: int
    schedule: list[ScheduleDay]


class ProviderAvailability(BaseModel):
    id: int
    provider_id: int
    clinic_id: int
    schedule: list[ScheduleDay]
    updated_at: datetime

    class Config:
        from_attributes = True


class ProviderAvailabilitySetup(BaseModel):
    clinic_id: int
    working_days: list[str]
    start_time: str
    end_time: str


class ScheduleDateStatusUpdate(BaseModel):
    date: str
    status: str