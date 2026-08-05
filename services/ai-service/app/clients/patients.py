from app.config import settings
from app.clients.http import make_request

PATIENT_SERVICE_URL = settings.PATIENT_SERVICE_URL


async def get_patient(patient_id: int) -> dict:
    response = await make_request("get", f"{PATIENT_SERVICE_URL}/patients/{patient_id}")
    return response.json()


async def get_all_patients() -> list:
    response = await make_request("get", f"{PATIENT_SERVICE_URL}/patients")
    return response.json()