from temporalio import activity
import httpx, os

_token = None

async def get_service_token(): #for internal auth
    global _token
    if _token:
        return _token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('AUTH_SERVICE_URL')}/login",
            data={
                "username": os.getenv("SYSTEM_EMAIL"),
                "password": os.getenv("SYSTEM_PASSWORD")
            }
        )
        response.raise_for_status()
        _token = response.json()["access_token"]
    return _token

@activity.defn
async def create_patient_record(user_data: dict):
    token = await get_service_token()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('PATIENT_SERVICE_URL')}/patients",
            json={"user_id": user_data["id"], "date_of_birth": user_data["date_of_birth"]},
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 401:
         # Token expired — clear cache and retry once
            _token = None
            token = await get_service_token()
            response = await client.post(
                f"{os.getenv('PATIENT_SERVICE_URL')}/patients",
                json={"user_id": user_data["id"], "date_of_birth": user_data["date_of_birth"]},
                headers={"Authorization": f"Bearer {token}"}
            )

        response.raise_for_status()