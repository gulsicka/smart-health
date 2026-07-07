from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class TokenData(BaseModel):
    user_id: int
    roles: list[str]


class RoleBase(BaseModel):
    role_name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    email: EmailStr
    number: Optional[str] = None
    role_ids: list[int]

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    number: Optional[str] = None
    role_ids: Optional[list[int]] = None

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    number: Optional[str] = None
    roles: list[Role]
    created_at: datetime
    class Config:
        from_attributes = True


class AuditLogBase(BaseModel):
    user_id: int
    action: str
    entity_type: str
    entity_id: int

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime
    class Config:
        from_attributes = True
