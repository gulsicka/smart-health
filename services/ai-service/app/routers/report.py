from fastapi import APIRouter, Depends, HTTPException
from app import schemas, auth
from app.enums import RoleName
from app.config import settings
from langchain_groq import ChatGroq
from app.agent import run_agent
import datetime
from app import kafka_producer
import uuid

router = APIRouter()

llm = ChatGroq(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL, temperature=0)

ID_RESOLUTION_NOTE = (
    " Any record you look up may contain IDs referencing other entities — a department_id, "
    "user_id, clinic_id, etc — never show a raw ID to the reader as if it were an answer. "
    "Always resolve it first: call get_department for a department_id, get_user for a user_id "
    "(name/email), get_clinic for a clinic_id, and so on, before including that information."
)

REPORT_INSTRUCTIONS = {
    "daily_appointments": (
        "Write a daily appointment summary report for {date}. First call "
        "get_daily_appointment_stats with that date to get the exact numbers and appointment "
        "records, then write the report from that. Focus on the appointment list, statuses, "
        "and providers."
    ),
    "department_utilization": (
        "Write a department utilization report. First call get_department_utilization_stats "
        "to get the exact numbers, then write the report from that. Focus on appointments and "
        "active providers per department."
    ),
    "patient_engagement": (
        "Write a patient engagement summary. First call get_patient_engagement_stats to get "
        "the exact numbers, then write the report from that. Focus on patient participation "
        "and appointment frequency."
    ),
    "executive_snapshot": (
        "Write an executive operational snapshot for {date}. First call "
        "get_executive_snapshot_stats with that date to get the exact numbers, then write the "
        "report from that. Focus on high-level totals and the cancellation rate."
    ),
}

SYSTEM_PROMPT = (
    "You are a healthcare operations analyst writing reports for hospital management.\n\n"
    "You have tools that return exact, pre-computed statistics for each report type — always "
    "call the relevant stats tool first (as instructed) and use those numbers exactly as "
    "returned. Never calculate, estimate, or re-derive a total, count, or percentage yourself, "
    "and never invent a patient, provider, or department that isn't in the tool's result. If a "
    "tool result already lists individual records, you may reference specific ones for detail, "
    "but never count or group them to produce a total — the stats tool's numbers always take "
    "priority over anything you might tally yourself.\n\n"
    "You also have tools to look up a specific patient, provider, clinic, department, or user "
    "if you need to confirm or add detail beyond what the stats tool gives you.\n\n"
    "Write a well-structured, professional report." + ID_RESOLUTION_NOTE
)


async def publish_report_event(user_id: int, report_type: str, status: str):  # counts toward overall "AI Assistant Usage" alongside chat/communication
    await kafka_producer.publish_event(
        event={
            "event_type": "ai.report",
            "report_type": report_type,
            "status": status,  # "answered" or "failed"
            "user_id": user_id,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
        key=str(user_id),
    )


@router.post("/generate/report", response_model=schemas.GenerateReportResponse)
async def generate_report(
    body: schemas.GenerateReportRequest,
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    date_str = body.date or datetime.date.today().isoformat()
    report_type = body.report_type.value
    status = "answered"

    if report_type not in REPORT_INSTRUCTIONS:
        raise HTTPException(status_code=400, detail="Unknown report type")

    try:
        query = REPORT_INSTRUCTIONS[report_type].format(date=date_str)
        content = await run_agent(llm, SYSTEM_PROMPT, query)
    except Exception:
        status = "failed"
        raise
    finally:
        await publish_report_event(current_user.user_id, report_type, status)

    return schemas.GenerateReportResponse(content=content)
