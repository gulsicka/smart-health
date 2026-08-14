from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app import schemas, auth
from app.enums import RoleName
from app.config import settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.tools import TOOLS, TOOLS_BY_NAME
from app import kafka_producer
from datetime import datetime
import uuid
import json

router = APIRouter()

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0,  # same context should always give the same answer, no random hedging
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

If a lookup returns nothing, say so plainly instead of making something up.
"""

MAX_TOOL_ITERATIONS = 5

llm_with_tools = llm.bind_tools(TOOLS)


async def publish_chat_event(user_id: int, status: str):  # one event per /chat call — feeds "questions asked/answered" analytics
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
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=query)]
    status = "answered"
    try:
        yield ": connected\n\n"

        for _ in range(MAX_TOOL_ITERATIONS):
            full = None
            async for chunk in llm_with_tools.astream(messages):
                full = chunk if full is None else full + chunk
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"

            messages.append(full)

            if not full.tool_calls:
                return  # already streamed the whole answer above, nothing left to do

            # smaller/faster tool-calling models can occasionally emit
            # duplicate calls to the exact same tool with the exact same args in one turn — dedupe
            # by (name, args) so a real lookup only ever runs once, while still answering every
            # tool_call_id the model emitted, since the API expects a response for each one
            seen_calls = {}
            for call in full.tool_calls:
                key = (call["name"], json.dumps(call["args"], sort_keys=True))

                if key not in seen_calls:
                    # a real, visible status event for each *distinct* tool call as it actually
                    # happens — not cosmetic filler, this is the genuine ReAct loop's tool-call
                    # step showing up live
                    yield f"data: [calling {call['name']}...]\n\n"

                    tool_fn = TOOLS_BY_NAME[call["name"]]
                    try:
                        result = await tool_fn.ainvoke(call["args"])
                    except Exception as e:
                        result = f"Error calling {call['name']}: {e}"
                    seen_calls[key] = result if isinstance(result, str) else json.dumps(result, default=str)

                messages.append(ToolMessage(content=seen_calls[key], tool_call_id=call["id"]))
        else:
            yield "data: I wasn't able to fully answer that within the allowed number of lookups — try rephrasing or narrowing your question.\n\n"
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
