from pydantic import BaseModel
from datetime import datetime, time
from typing import Optional


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
    pass

class Provider(ProviderBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class ProviderAvailabilityBase(BaseModel):
    provider_id: int
    clinic_id: int
    day_of_week: str   # "Monday", "Tuesday", etc.
    start_time: time
    end_time: time

class ProviderAvailabilityCreate(ProviderAvailabilityBase):
    pass

class ProviderAvailability(ProviderAvailabilityBase):
    id: int
    class Config:
        from_attributes = True
