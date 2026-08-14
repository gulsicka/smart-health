from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app import schemas, auth
from app.enums import RoleName
from app.config import settings
from langchain_groq import ChatGroq
from app.agent import stream_agent
from app import kafka_producer
from datetime import datetime
import uuid

router = APIRouter()

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0,
    streaming=True,
)

SYSTEM_PROMPT = """You are a helpful assistant for SmartHealth, a healthcare management platform.

You have tools to look up live data (patients, providers, clinics, departments, users, and
appointments) and a tool to search hospital policy/handbook documents. Always call a tool to
get real data before answering a question about a specific entity — never guess or invent an
ID, name, or number. Use search_documents for general hospital-knowledge questions (policies,
procedures, guidelines), and the entity lookup tools for anything about a specific patient,
provider, clinic, department, user, or appointment.

Patient and provider records only contain a user_id, not a name or email — they do NOT store
that themselves. Whenever a question needs a patient's or provider's name, email, or other
account info, first get the patient/provider record, then call get_user with the user_id found
in that record to fetch their actual name and email. Never guess a name from an ID alone.

Any record you look up may contain other IDs too — a department_id, clinic_id, etc — never show
a raw ID to the user as if it were an answer, always resolve it via the matching tool first.

If a lookup returns nothing, say so plainly instead of making something up.
"""


async def publish_chat_event(user_id: int, status: str):
    await kafka_producer.publish_event(
        event={
            "event_type": "ai.chat",
            "status": status,
            "user_id": user_id,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        },
        key=str(user_id),
    )


async def stream_response(query: str, user_id: int):
    status = "answered"
    try:
        async for line in stream_agent(llm, SYSTEM_PROMPT, query):
            yield line
    except Exception:
        status = "failed"
        raise
    finally:
        await publish_chat_event(user_id, status)


@router.post("/chat")
async def chat(
    body: schemas.ChatRequest,
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    return StreamingResponse(
        stream_response(body.query, current_user.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",  # tells the client not to wait for/cache a full response before rendering
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disables buffering on any proxy sitting in front (nginx etc)
        },
    )
