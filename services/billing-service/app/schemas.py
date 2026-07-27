from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.enums import InvoiceStatus, RoleName


class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


class InvoiceOut(BaseModel):
    id: int
    appointment_id: int
    patient_id: int
    provider_id: int
    clinic_id: int
    amount: Decimal
    status: InvoiceStatus
    appointment_date: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
