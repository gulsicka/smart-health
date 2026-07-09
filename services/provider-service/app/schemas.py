from pydantic import BaseModel, validator
from datetime import datetime, time, date
from typing import Optional

VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

class TokenData(BaseModel):
    user_id: int
    roles: list[str]


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
    class Config:
        from_attributes = True


class ProviderAvailabilityBase(BaseModel):
    provider_id: int
    clinic_id: int
    date: date   # "Monday", "Tuesday", etc.
    start_time: time
    end_time: time

class ProviderAvailabilityCreate(ProviderAvailabilityBase):
    pass

class ProviderAvailability(ProviderAvailabilityBase):
    id: int
    class Config:
        from_attributes = True


class ProviderAvailabilitySetup(BaseModel):
    clinic_id: int
    working_days: list[str]
    start_time: str  # "HH:MM:SS"
    end_time: str    
