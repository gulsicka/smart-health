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

async def extract_pdf_pages(source: str, pdf_base64: str) -> list:
    response = await make_request(
        "post",
        f"{AI_SERVICE_URL}/internal/pdf/extract",
        json={"source": source, "pdf_base64": pdf_base64},
        timeout=250.0,
    )
    return response.json()["pages"]


async def get_page_hashes(source: str) -> dict:
    response = await make_request("get", f"{AI_SERVICE_URL}/internal/pdf/page-hashes", params={"source": source})
    return response.json()["page_hashes"]


async def process_pdf_page(source: str, page_number: int, text: str, page_hash: str) -> int:
    response = await make_request(
        "post",
        f"{AI_SERVICE_URL}/internal/pdf/page",
        json={"source": source, "page_number": page_number, "text": text, "page_hash": page_hash},
        timeout=55.0,
    )
    return response.json()["chunks_stored"]


async def delete_pdf_page(source: str, page_number: int):
    await make_request(
        "post",
        f"{AI_SERVICE_URL}/internal/pdf/delete-page",
        json={"source": source, "page_number": page_number},
    )
