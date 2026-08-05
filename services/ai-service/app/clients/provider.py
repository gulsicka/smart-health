from app.config import settings
from app.clients.http import make_request

PROVIDER_SERVICE_URL = settings.PROVIDER_SERVICE_URL


async def get_provider(provider_id: int) -> dict:
    response = await make_request("get", f"{PROVIDER_SERVICE_URL}/providers/{provider_id}")
    return response.json()


async def get_all_providers() -> list:
    response = await make_request("get", f"{PROVIDER_SERVICE_URL}/providers")
    return response.json()


async def get_all_clinics() -> list:
    response = await make_request("get", f"{PROVIDER_SERVICE_URL}/clinics")
    return response.json()


async def get_all_departments() -> list:
    response = await make_request("get", f"{PROVIDER_SERVICE_URL}/departments")
    return response.json()


async def get_clinic(clinic_id: int) -> dict:
    response = await make_request("get", f"{PROVIDER_SERVICE_URL}/clinics/{clinic_id}")
    return response.json()


async def get_department(department_id: int) -> dict:
    response = await make_request("get", f"{PROVIDER_SERVICE_URL}/departments/{department_id}")
    return response.json()
