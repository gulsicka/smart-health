from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Many-to-many junction: users ↔ roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, nullable=False, unique=True)
    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
