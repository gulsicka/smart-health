from app.config import settings
from app.clients.http import make_request

APPOINTMENT_SERVICE_URL = settings.APPOINTMENT_SERVICE_URL


async def get_all_appointments() -> list:
    response = await make_request("get", f"{APPOINTMENT_SERVICE_URL}/appointments")
    return response.json()


async def get_appointment(appointment_id: int) -> dict:
    response = await make_request("get", f"{APPOINTMENT_SERVICE_URL}/appointments/{appointment_id}")
    return response.json()


async def get_appointments_by_patient(patient_id: int) -> list:
    response = await make_request("get", f"{APPOINTMENT_SERVICE_URL}/patients/{patient_id}/appointments")
    return response.json()


async def get_appointments_by_provider(provider_id: int) -> list:
    response = await make_request("get", f"{APPOINTMENT_SERVICE_URL}/providers/{provider_id}/appointments")
    return response.json()


async def get_appointments_by_clinic(clinic_id: int) -> list:
    response = await make_request("get", f"{APPOINTMENT_SERVICE_URL}/clinics/{clinic_id}/appointments")
    return response.json()
