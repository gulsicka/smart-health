from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserInput:
    id: int
    roles: list[str]
    date_of_birth: Optional[str] = None
    department_id: Optional[int] = None


@dataclass
class UserIdInput:
    user_id: int


@dataclass
class NotifyUserInput:
    user_id: int
    roles: list[str]


@dataclass
class AppointmentInput:
    patient_id: int
    provider_id: int
    clinic_id: int
    date: str
    start_time: str
    end_time: str


@dataclass
class ProviderScheduleInput:
    provider_id: int
    clinic_id: int
    working_days: list[str]
    start_time: str
    end_time: str


@dataclass
class FailedWorkflowInput:
    error: str


@dataclass
class AppointmentReminderInput:
    appointment_id: int
    patient_id: int
    provider_id: int
    clinic_id: int
    date: str
    start_time: str
    end_time: str
