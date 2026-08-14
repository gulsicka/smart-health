from langchain_core.tools import tool
from app.database import SessionLocal
from app import crud
from app.clients import patients as patients_client, provider as provider_client, appointment as appointment_client
from app.clients import auth as auth_client

@tool
async def get_patient(patient_id: int) -> dict:
    """Look up a single patient's record by their patient ID."""
    return await patients_client.get_patient(patient_id)


@tool
async def get_provider(provider_id: int) -> dict:
    """Look up a single provider's record by their provider ID."""
    return await provider_client.get_provider(provider_id)


@tool
async def get_clinic(clinic_id: int) -> dict:
    """Look up a single clinic's info by its clinic ID."""
    return await provider_client.get_clinic(clinic_id)


@tool
async def get_department(department_id: int) -> dict:
    """Look up a single department's info by its department ID."""
    return await provider_client.get_department(department_id)


@tool
async def get_user(user_id: int) -> dict:
    """Look up a user account's name and email by user ID — patient and provider records only
    store a user_id, not the name/email itself, so use this whenever a question needs a name."""
    return await auth_client.get_user(user_id)


@tool
async def get_appointment(appointment_id: int) -> dict:
    """Look up a single appointment's details by its appointment ID."""
    return await appointment_client.get_appointment(appointment_id)


@tool
async def get_appointments_by_patient(patient_id: int) -> list:
    """Get every appointment belonging to one specific patient, by their patient ID."""
    return await appointment_client.get_appointments_by_patient(patient_id)


@tool
async def get_appointments_by_provider(provider_id: int) -> list:
    """Get every appointment belonging to one specific provider, by their provider ID."""
    return await appointment_client.get_appointments_by_provider(provider_id)


@tool
async def get_appointments_by_clinic(clinic_id: int) -> list:
    """Get every appointment at one specific clinic, by its clinic ID."""
    return await appointment_client.get_appointments_by_clinic(clinic_id)


@tool
def search_documents(query: str) -> str:
    """Search ingested hospital policy/handbook PDF documents. Use this for general
    hospital-knowledge questions, not for questions about a specific patient, provider, or
    appointment."""
    db = SessionLocal()
    try:
        results = crud.retrieve_chunks(db, query, top_k=5)
        if not results:
            return "No matching document content found."
        return "\n\n".join(row.content for row, score in results)
    finally:
        db.close()


TOOLS = [
    get_patient, get_provider, get_clinic, get_department, get_user, get_appointment,
    get_appointments_by_patient, get_appointments_by_provider, get_appointments_by_clinic,
    search_documents,
]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
