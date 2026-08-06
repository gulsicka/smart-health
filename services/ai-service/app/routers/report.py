from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, auth, crud
from app.database import get_db
from app.enums import RoleName, ReportType
from app.config import settings
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
    "The data below has clearly labeled sections:\n\n"
    "1. SUMMARY STATISTICS — pre-computed, exact totals, counts, and percentages. "
    "These numbers are already correct and final. Whenever you state any total, count, "
    "or percentage in your report, copy it directly from this section. Never calculate, "
    "estimate, or re-derive a number yourself.\n\n"
    "2. INDIVIDUAL APPOINTMENT RECORDS (when present) — the raw list of individual appointments, "
    "given so you can reference specific providers, times, and patterns in your writing. "
    "This section is for descriptive detail ONLY. Do NOT count or group these lines to "
    "produce any total, provider count, or department count — those are already given to "
    "you, correctly, in SUMMARY STATISTICS above, and they always take priority over "
    "anything you might tally yourself. An appointment's ID number is just a database "
    "identifier, never a count.\n\n"
    "Never invent a patient, provider, or department that does not literally appear in the "
    "data below. If a count in SUMMARY STATISTICS is higher than the number of named entries "
    "you can see, do NOT fabricate additional unnamed ones to make the numbers match — just "
    "report the named entries you actually have and the total exactly as given.\n\n"
    "Write a well-structured, professional report that uses specific details from the "
    "individual records where relevant, while always reporting totals/counts exactly as "
    "given in SUMMARY STATISTICS.\n\nData:\n{context}"
)


def build_context(report_type: str, stats_chunk, records_chunk) -> str:
    #framing/labeling lives here, at prompt-build time — never stored in pgvector itself
    context = "=== SUMMARY STATISTICS (authoritative — always use these exact numbers) ===\n" + stats_chunk.content
    if records_chunk:
        context += (
            "\n\n=== INDIVIDUAL APPOINTMENT RECORDS (descriptive detail only — do NOT count these lines) ===\n"
            + records_chunk.content
        )
    return context


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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    date_str = body.date or datetime.date.today().isoformat()
    report_type = body.report_type.value

    if report_type == "daily_appointments":
        stats_source = f"report-daily_appointments-{date_str}"
        records_source = f"report-daily_appointments-{date_str}-records"
    elif report_type == "executive_snapshot":
        stats_source = f"report-executive_snapshot-{date_str}"
        records_source = None
    elif report_type == "department_utilization":
        stats_source = "report-department_utilization"
        records_source = None
    elif report_type == "patient_engagement":
        stats_source = "report-patient_engagement"
        records_source = None
    else:
        raise HTTPException(status_code=400, detail="Unknown report type")

    stats_chunk = crud.get_existing_chunk(db, stats_source)
    if not stats_chunk:
        raise HTTPException(
            status_code=404,
            detail=f"No cached report data for '{report_type}'"
                   + (f" on {date_str}" if body.report_type in (ReportType.daily_appointments, ReportType.executive_snapshot) else "")
                   + " — run /ingest/sync first.",
        )
    records_chunk = crud.get_existing_chunk(db, records_source) if records_source else None

    context = build_context(report_type, stats_chunk, records_chunk)
    content = await generate_report_text(context, REPORT_INSTRUCTIONS[report_type])
    return schemas.GenerateReportResponse(content=content)
