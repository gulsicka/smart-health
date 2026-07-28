from clients.common.http import make_request
from config import settings

PROVIDER_URL = settings.PROVIDER_SERVICE_URL


async def create_provider(user_id: int, department_id: int | None):
    await make_request(
        "post",
        f"{PROVIDER_URL}/providers",
        json={"user_id": user_id, "department_id": department_id},
    )


async def get_provider(provider_id: int):
    return await make_request("get", f"{PROVIDER_URL}/providers/{provider_id}")


async def get_department(department_id: int):
    return await make_request("get", f"{PROVIDER_URL}/departments/{department_id}")


async def get_clinic(clinic_id: int):
    return await make_request("get", f"{PROVIDER_URL}/clinics/{clinic_id}")


async def get_provider_availability(provider_id: int):
    return await make_request("get", f"{PROVIDER_URL}/providers/{provider_id}/availability")


async def delete_provider_by_user_id(user_id: int):
    await make_request("delete", f"{PROVIDER_URL}/providers/by-user-id/{user_id}")


async def upsert_availability(provider_id: int, clinic_id: int, schedule: list[dict]):
    await make_request(
        "post",
        f"{PROVIDER_URL}/providers/{provider_id}/availability",
        json={
            "clinic_id": clinic_id,
            "schedule": schedule,
        },
    )
