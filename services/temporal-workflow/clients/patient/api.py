from clients.common.http import make_request
from config import settings

PATIENT_URL = settings.PATIENT_SERVICE_URL


async def create_patient(user_id: int, date_of_birth: str):
    await make_request(
        "post",
        f"{PATIENT_URL}/patients",
        json={"user_id": user_id, "date_of_birth": date_of_birth},
    )


async def delete_patient_by_user_id(user_id: int):
    await make_request("delete", f"{PATIENT_URL}/patients/by-user-id/{user_id}")


async def get_patient(patient_id: int):
    return await make_request("get", f"{PATIENT_URL}/patients/{patient_id}")
