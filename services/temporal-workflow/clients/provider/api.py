import os
from clients.common.http import make_request

PROVIDER_URL = os.getenv("PROVIDER_SERVICE_URL")


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


async def create_availability(provider_id: int, clinic_id: int, date: str, start_time: str, end_time: str):
    await make_request(
        "post",
        f"{PROVIDER_URL}/providers/{provider_id}/availability",
        json={
            "provider_id": provider_id,
            "clinic_id": clinic_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
        },
    )
