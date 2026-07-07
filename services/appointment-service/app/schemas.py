from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional


class TokenData(BaseModel):
    user_id: int
    roles: list[str]


class AppointmentCreate(BaseModel):
    patient_id: int
    provider_id: int
    clinic_id: int
    department_id: int
    date: date
    start_time: time
    end_time: time


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None


class Appointment(AppointmentCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookedSlot(BaseModel):
    appointment_id: int
    start_time: time
    end_time: time
    status: str
