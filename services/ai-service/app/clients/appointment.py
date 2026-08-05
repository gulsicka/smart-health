from app.config import settings
from app.clients.http import make_request

APPOINTMENT_SERVICE_URL = settings.APPOINTMENT_SERVICE_URL


async def get_all_appointments() -> list:
    response = await make_request("get", f"{APPOINTMENT_SERVICE_URL}/appointments")
    return response.json()
