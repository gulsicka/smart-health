import os
from clients.common.http import make_request

APPOINTMENT_URL = os.getenv("APPOINTMENT_SERVICE_URL")


async def get_appointments():
    return await make_request("get", f"{APPOINTMENT_URL}/appointments")


async def create_appointment_internal(appointment: dict):
    await make_request(
        "post",
        f"{APPOINTMENT_URL}/appointments/internal",
        json=appointment,
    )
