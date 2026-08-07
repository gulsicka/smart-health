from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, auth, crud
from app.database import get_db
from app.enums import RoleName, CommunicationType
from app.config import settings
from langchain_groq import ChatGroq
from app.utils.helpers import build_context
from app import kafka_producer
from datetime import datetime
import uuid

router = APIRouter()

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    streaming=False,
)

PROMPTS = {
    CommunicationType.follow_up: "You are a healthcare assistant. Write a post-appointment follow-up message for a patient. Focus on recovery tips, next steps after the visit, and encouraging them to book a follow-up appointment if needed. Do not mention upcoming or future appointments.",
    CommunicationType.service_recommendation: "You are a healthcare assistant. Based on the context below, recommend the most suitable healthcare services or specialists for the patient. Be specific and helpful.",
    CommunicationType.preventive_care: "You are a healthcare assistant. Write a preventive care suggestion message for a patient based on the context below. Focus on actionable health tips and screenings relevant to their profile.",
    CommunicationType.operational_assistance: "You are a healthcare operations assistant. Based on the context below, provide a clear and concise operational assistance response suitable for healthcare staff.",
}

async def publish_communication_event(user_id: int, communication_type: str, status: str):#feeds "generated communication usage" analytics, broken down by type
    await kafka_producer.publish_event(
        event={
            "event_type": "ai.communication",
            "communication_type": communication_type,
            "status": status,
            "user_id": user_id,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        },
        key=str(user_id),
    )


def get_response(body: schemas.GenerateCommunicationRequest, db: Session):
    prompt = PROMPTS[body.type]

    if body.patient_id:
        source_prefix = f"patient-{body.patient_id}"
    elif body.provider_id:
        source_prefix = f"provider-{body.provider_id}"
    elif body.clinic_id:
        source_prefix = f"clinic-{body.clinic_id}"
    else:
        source_prefix = None


    results = crud.retrieve_chunks(db, body.type.value, body.top_k, source_prefix=source_prefix)
    chunks = [row for row, score in results]

    context = build_context(chunks)
    response = llm.invoke([
        ("system", prompt),
        ("human", context),
        ])
    return response.content

@router.post("/generate/communication")
async def generate_communication(
    body: schemas.GenerateCommunicationRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    status = "answered"
    try:
        content = get_response(body, db)
    except Exception:
        status = "failed"
        raise
    finally:
        await publish_communication_event(current_user.user_id, body.type.value, status)
    return schemas.GenerateCommunicationResponse(content=content)


@router.post("/generate/reminder")
def generate_reminder(
    body: schemas.GenerateReminderRequest,
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    timing = "tomorrow" if body.reminder_type == "day_before" else "in 1 hour"
    context = (
        f"Patient ID {body.patient_id} has an appointment (ID: {body.appointment_id}) "
        f"with Provider ID {body.provider_id} at Clinic ID {body.clinic_id} "
        f"on {body.date} starting at {body.start_time}. "
        f"The appointment is {timing}."
    )
    prompt = (
        f"You are a healthcare assistant. Write a short, friendly appointment reminder message "
        f"for a patient whose appointment is {timing}. Use only the details provided. "
        f"Do not use placeholders. Sign off as SmartHealth."
    )
    response = llm.invoke([("system", prompt), ("human", context)])
    return schemas.GenerateReminderResponse(content=response.content)
