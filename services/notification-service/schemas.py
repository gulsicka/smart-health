from datetime import datetime

from pydantic import BaseModel

from enums import RoleName


class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


class NotificationOut(BaseModel):
    id: int
    user_id: int
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
