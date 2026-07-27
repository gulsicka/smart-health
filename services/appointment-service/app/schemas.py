from pydantic import BaseModel, validator
from app.enums import RoleName, AppointmentStatus
from datetime import datetime, date, time
from typing import Optional, TypedDict



class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


class AppointmentBase(BaseModel):
    patient_id: int
    provider_id: int
    clinic_id: int
    date: date
    start_time: time
    end_time: time


class AppointmentCreate(AppointmentBase):
    @validator('start_time')
    def must_be_future(cls, v, values):
        appointment_dt = datetime.combine(values['date'], v)
        if appointment_dt <= datetime.utcnow():
            raise ValueError('Appointment date and time must be in the future')
        return v


class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None


class Appointment(AppointmentBase):
    id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookedSlot(BaseModel):
    appointment_id: int
    start_time: time
    end_time: time
    status: AppointmentStatus


class WorkflowAppointmentInput(TypedDict):
    patient_id: int
    provider_id: int
    clinic_id: int
    date: str
    start_time: str
    end_time: str
