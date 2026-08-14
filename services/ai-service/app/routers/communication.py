from fastapi import APIRouter, Depends
from app import schemas, auth
from app.enums import RoleName, CommunicationType
from app.config import settings
from langchain_groq import ChatGroq
from app.agent import run_agent
from app import kafka_producer
from datetime import datetime
import uuid

router = APIRouter()

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0,
)

ID_RESOLUTION_NOTE = (
    " Any record you look up may contain IDs referencing other entities — a department_id, "
    "user_id, clinic_id, etc — never show a raw ID to the reader as if it were an answer. "
    "Always resolve it first: call get_department for a department_id, get_user for a user_id "
    "(name/email), get_clinic for a clinic_id, and so on, before including that information."
)

PROMPTS = {
    CommunicationType.follow_up: "You are a healthcare assistant. Use your tools to look up the real patient this message is for — never invent a name or detail. Write a post-appointment follow-up message for that patient. Focus on recovery tips, next steps after the visit, and encouraging them to book a follow-up appointment if needed. Do not mention upcoming or future appointments." + ID_RESOLUTION_NOTE,
    CommunicationType.service_recommendation: "You are a healthcare assistant. Use your tools to look up the real patient or entity this is about — never invent a name or detail. Recommend the most suitable healthcare services or specialists for them. Be specific and helpful." + ID_RESOLUTION_NOTE,
    CommunicationType.preventive_care: "You are a healthcare assistant. Use your tools to look up the real patient this is for — never invent a name or detail. Write a preventive care suggestion message based on their actual profile. Focus on actionable health tips and screenings relevant to them." + ID_RESOLUTION_NOTE,
    CommunicationType.operational_assistance: "You are a healthcare operations assistant. Use your tools to look up any real entity referenced in the request — never invent a name or detail. Provide a clear and concise operational assistance response suitable for healthcare staff." + ID_RESOLUTION_NOTE,
}


async def publish_communication_event(user_id: int, communication_type: str, status: str): 
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


def build_query(body: schemas.GenerateCommunicationRequest) -> str:
    if body.patient_id:
        return f"This message is for patient ID {body.patient_id}."
    if body.provider_id:
        return f"This message is for provider ID {body.provider_id}."
    if body.clinic_id:
        return f"This message is for clinic ID {body.clinic_id}."
    return "No specific patient, provider, or clinic was specified."


@router.post("/generate/communication")
async def generate_communication(
    body: schemas.GenerateCommunicationRequest,
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    status = "answered"
    try:
        content = await run_agent(llm, PROMPTS[body.type], build_query(body))
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
