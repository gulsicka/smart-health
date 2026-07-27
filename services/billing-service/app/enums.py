from enum import Enum


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"


class RoleName(str, Enum):
    ADMIN = "admin"
    PATIENT = "patient"
    PROVIDER = "provider"
    FD_STAFF = "fd_staff"
