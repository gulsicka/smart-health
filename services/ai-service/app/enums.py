from enum import Enum


class RoleName(str, Enum):
    ADMIN    = "admin"
    PATIENT  = "patient"
    PROVIDER = "provider"
    FD_STAFF = "fd_staff"

class CommunicationType(str, Enum):
    follow_up = "follow_up"
    service_recommendation = "service_recommendation"
    preventive_care = "preventive_care"
    operational_assistance = "operational_assistance"

class ReportType(str, Enum):
    daily_appointments = "daily_appointments"
    department_utilization = "department_utilization"
    patient_engagement = "patient_engagement"
    executive_snapshot = "executive_snapshot"