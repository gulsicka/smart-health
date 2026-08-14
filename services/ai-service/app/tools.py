from langchain_core.tools import tool
from app.database import SessionLocal
from app import crud
from app.clients import patients as patients_client, provider as provider_client, appointment as appointment_client
from app.clients import auth as auth_client
from app.utils import report_text

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


async def _report_maps():
    # bulk fetch, used only inside the report stat tools below — never exposed to the LLM
    # directly as raw data, only as the pre-computed numbers report_text.py builds from it
    all_users = await auth_client.get_all_users()
    user_map = {u["id"]: u for u in all_users}
    all_depts = await provider_client.get_all_departments()
    dept_map = {d["id"]: d for d in all_depts}
    all_clinics = await provider_client.get_all_clinics()
    all_patients = await patients_client.get_all_patients()
    all_providers = await provider_client.get_all_providers()
    provider_map = {p["id"]: p for p in all_providers}
    all_appointments = await appointment_client.get_all_appointments()
    return all_appointments, all_providers, all_depts, all_clinics, all_patients, provider_map, dept_map, user_map


@tool
async def get_daily_appointment_stats(date: str) -> str:
    """Get exact, pre-computed statistics and individual appointment records for a single date
    (format YYYY-MM-DD): totals, status breakdown, cancellation rate, and a provider/department
    breakdown for that date. Use this for daily appointment summary reports. These numbers are
    already correct and final — never recalculate or estimate them yourself, just report them."""
    all_appointments, all_providers, all_depts, all_clinics, all_patients, provider_map, dept_map, user_map = await _report_maps()
    stats_text, records_text = report_text.build_daily_report(
        date, all_appointments, all_providers, all_depts, all_clinics, all_patients,
        provider_map, dept_map, user_map,
    )
    return stats_text + "\n\nIndividual appointment records for that date:\n" + records_text


@tool
async def get_executive_snapshot_stats(date: str) -> str:
    """Get exact, pre-computed high-level operational totals for a single date (format
    YYYY-MM-DD): patient/provider/department/clinic/appointment totals, status breakdown,
    cancellation rate, and the busiest department that day. Use this for executive operational
    snapshot reports. These numbers are already correct and final — never recalculate or
    estimate them yourself, just report them."""
    all_appointments, all_providers, all_depts, all_clinics, all_patients, provider_map, dept_map, _ = await _report_maps()
    return report_text.build_executive_snapshot(
        date, all_appointments, all_providers, all_depts, all_clinics, all_patients,
        provider_map, dept_map,
    )


@tool
async def get_department_utilization_stats() -> str:
    """Get exact, pre-computed department utilization statistics across all time: appointment
    count, active provider count, and busiest provider per department. Use this for department
    utilization reports. These numbers are already correct and final — never recalculate or
    estimate them yourself, just report them."""
    all_appointments, _, all_depts, _, _, provider_map, _, user_map = await _report_maps()
    return report_text.build_department_utilization(all_appointments, all_depts, provider_map, user_map)


@tool
async def get_patient_engagement_stats() -> str:
    """Get exact, pre-computed patient engagement statistics across all time: total/engaged/
    zero-appointment patient counts, average appointments per patient, and the top 5 most
    engaged patients. Use this for patient engagement reports. These numbers are already
    correct and final — never recalculate or estimate them yourself, just report them."""
    all_appointments, _, _, _, all_patients, _, _, user_map = await _report_maps()
    return report_text.build_patient_engagement(all_appointments, all_patients, user_map)


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
    get_daily_appointment_stats, get_executive_snapshot_stats,
    get_department_utilization_stats, get_patient_engagement_stats,
]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
