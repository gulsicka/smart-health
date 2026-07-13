from enum import Enum

class RoleName(str, Enum):
    ADMIN    = "admin"
    PATIENT  = "patient"
    PROVIDER = "provider"
    FD_STAFF = "fd_staff"

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE  = "active"
