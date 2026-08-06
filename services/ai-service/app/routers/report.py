from fastapi import APIRouter, Depends
from app import schemas, auth
from app.enums import RoleName
from app.config import settings
from app.clients import provider as provider_client
from app.clients import patients as patients_client
from app.clients import appointment as appointment_client
from app.clients import auth as auth_client
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import datetime

router = APIRouter()

llm = ChatGroq(api_key=settings.GROQ_API_KEY, model="llama-3.1-8b-instant", streaming=True)

REPORT_INSTRUCTIONS = {
    "daily_appointments":     "Write a daily appointment summary for the given date. Focus on the appointment list, statuses, and providers.",
    "department_utilization": "Write a department utilization report. Focus on appointments and active providers per department.",
    "patient_engagement":     "Write a patient engagement summary. Focus on patient participation and appointment frequency.",
    "executive_snapshot":     "Write an executive operational snapshot. Focus on high-level totals and the cancellation rate.",
}

SYSTEM_PROMPT = (
    "You are a healthcare operations analyst writing a detailed report for hospital management.\n\n"
    "The data below has two clearly labeled sections:\n\n"
    "1. SUMMARY STATISTICS — pre-computed, exact totals, counts, and percentages. "
    "These numbers are already correct and final. Whenever you state any total, count, "
    "or percentage in your report, copy it directly from this section. Never calculate, "
    "estimate, or re-derive a number yourself.\n\n"
    "2. INDIVIDUAL APPOINTMENT RECORDS — the raw list of individual appointments, given so "
    "you can reference specific providers, times, and patterns in your writing. "
    "This section is for descriptive detail ONLY. Do NOT count the lines in this list to "
    "produce a total — the correct totals are already given to you in SUMMARY STATISTICS above, "
    "and they always take priority over anything you might count yourself. "
    "An appointment's ID number is just a database identifier, never a count.\n\n"
    "Write a well-structured, professional report that uses specific details from the "
    "individual records where relevant, while always reporting totals/counts exactly as "
    "given in SUMMARY STATISTICS.\n\nData:\n{context}"
)


def totals_stats(date_str, daily, appointments, providers, departments, clinics, patients):#total counts for all entities for a specific date
    return [
        f"Report date: {date_str}",
        f"Total patients: {len(patients)}",
        f"Total providers: {len(providers)}",
        f"Total departments: {len(departments)}",
        f"Total clinics: {len(clinics)}",
        f"Total appointments (all time): {len(appointments)}",
        f"Appointments on {date_str}: {len(daily)}",
        "",
    ]


def day_status_stats(daily):#(specific date)count for all statuses of the appointments and also the cancelation r8
    statuses = {}
    for a in daily:
        statuses[a["status"]] = statuses.get(a["status"], 0) + 1

    cancelled = statuses.get("cancelled", 0)
    rate = (cancelled / len(daily) * 100) if daily else 0

    return [
        "Status counts for the day: " + (", ".join(f"{k}={v}" for k, v in statuses.items()) or "none"),
        f"Cancellation rate for the day: {rate:.1f}%",
        "",
    ]


def department_stats(appointments, departments, provider_map):#(all time)get total appointments per department and providers to whom the app is assigned
    lines = []
    for dept in departments:
        dept_appts = []
        for a in appointments:
            provider = provider_map.get(a["provider_id"], {})
            provider_dept_id = provider.get("department_id")
            if provider_dept_id == dept["id"]:
                dept_appts.append(a)
        active = len({a["provider_id"] for a in dept_appts})
        lines.append(f"Department {dept['name']}: {len(dept_appts)} appointments, {active} active providers")
    lines.append("")
    return lines


def engagement_stats(appointments, patients):#(all time)get patient stats for appointments
    counts = {}
    for a in appointments:
        counts[a["patient_id"]] = counts.get(a["patient_id"], 0) + 1

    engaged = sum(1 for p in patients if counts.get(p["id"], 0) > 0)
    avg = (len(appointments) / len(patients)) if patients else 0

    return [
        f"Patients with at least one appointment: {engaged}",
        f"Patients with none: {len(patients) - engaged}",
        f"Average appointments per patient: {avg:.1f}",
        "",
    ]


def day_appointment_lines(daily, provider_map, dept_map, user_map):#get app details wiht provider, dept names, status, start time etc
    lines = []
    for a in daily:
        prov      = provider_map.get(a["provider_id"], {})
        prov_name = user_map.get(prov.get("user_id"), {}).get("name", "Unknown")
        dept_name = dept_map.get(prov.get("department_id"), {}).get("name", "Unknown")
        lines.append(f"- Appt {a['id']} at {a['start_time']}: {prov_name} ({dept_name}), status {a['status']}")
    return lines


def build_stats(date_str, appointments, providers, departments, clinics, patients, users):
    provider_map = {p["id"]: p for p in providers}
    dept_map     = {d["id"]: d for d in departments}
    user_map     = {u["id"]: u for u in users}

    daily = [a for a in appointments if str(a["date"]).startswith(date_str)]#appointments for a specific date

    narrative_lines = (
        totals_stats(date_str, daily, appointments, providers, departments, clinics, patients)
        + day_status_stats(daily)
        + department_stats(appointments, departments, provider_map)
        + engagement_stats(appointments, patients)
    )
    narrative_context = "\n".join(narrative_lines)

    appointment_list_text = "\n".join(day_appointment_lines(daily, provider_map, dept_map, user_map))

    # both sections go to the LLM, but clearly labeled and separated so it knows
    # SUMMARY STATISTICS is authoritative and the record list is detail-only, never a count source
    full_context = (
        "=== SUMMARY STATISTICS (authoritative — always use these exact numbers) ===\n"
        + narrative_context
        + "\n\n=== INDIVIDUAL APPOINTMENT RECORDS (descriptive detail only — do NOT count these lines) ===\n"
        + (appointment_list_text or "No appointments recorded for this date.")
    )

    return full_context


async def generate_report_text(context: str, instruction: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{instruction}"),
    ])
    result = await (prompt | llm).ainvoke({"context": context, "instruction": instruction})
    return result.content


@router.post("/generate/report", response_model=schemas.GenerateReportResponse)
async def generate_report(
    body: schemas.GenerateReportRequest,
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    date_str = body.date or datetime.date.today().isoformat()

    context = build_stats(
        date_str,
        await appointment_client.get_all_appointments(),
        await provider_client.get_all_providers(),
        await provider_client.get_all_departments(),
        await provider_client.get_all_clinics(),
        await patients_client.get_all_patients(),
        await auth_client.get_all_users(),
    )

    print("=== CONTEXT SENT TO LLM ===")
    print(context)
    print("=== END CONTEXT ===")

    content = await generate_report_text(context, REPORT_INSTRUCTIONS[body.report_type.value])
    return schemas.GenerateReportResponse(content=content)