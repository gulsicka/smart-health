from enum import Enum


class RoleName(str, Enum):
    ADMIN    = "admin"
    PATIENT  = "patient"
    PROVIDER = "provider"
    FD_STAFF = "fd_staff"


class AppointmentStatus(str, Enum):
    REQUESTED   = "requested"
    CONFIRMED   = "confirmed"
    CHECKED_IN  = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    NO_SHOW     = "no_show"
    CANCELLED   = "cancelled"
    FAILED      = "failed"
