from clients.common.http import make_request
from config import settings

AI_SERVICE_URL = settings.AI_SERVICE_URL


async def generate_reminder(appointment_id: int, patient_id: int, provider_id: int, clinic_id: int, date: str, start_time: str, reminder_type: str) -> str:
    response = await make_request(
        "post",
        f"{AI_SERVICE_URL}/generate/reminder",
        json={
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "clinic_id": clinic_id,
            "date": date,
            "start_time": start_time,
            "reminder_type": reminder_type,
        },
    )
    return response.json()["content"]
