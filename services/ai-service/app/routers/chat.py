from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app import schemas, auth, crud
from app.database import get_db
from app.enums import RoleName
from app.config import settings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.utils.helpers import build_context
from app import kafka_producer
from datetime import datetime
import uuid

router = APIRouter()

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    streaming=True,
    temperature=0,#same context should always give the same answer, no random hedging
)

SYSTEM_PROMPT = """You are a helpful assistant for SmartHealth, a healthcare management platform.
Answer the user's question using only the context provided below.

The context below is EVERY chunk retrieved for this query — nothing is being held back from you.
If it contains records relevant to the question (e.g. appointment entries), count or use them
directly and give a direct, confident answer. Do not say you "lack information" or "cannot verify"
just because the context is short — a single relevant record is still a complete answer for that
record. Only say the context is insufficient if it truly contains nothing related to the question.

Context:
{context}"""


async def publish_chat_event(user_id: int, status: str):#one event per /chat call — feeds "questions asked/answered" analytics
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


async def stream_response(query: str, context: str, user_id: int):
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{query}"),
    ])
    chain = prompt | llm
    status = "answered"
    try:
        async for chunk in chain.astream({"context": context, "query": query}):
            if chunk.content:
                yield f"data: {chunk.content}\n\n"
    except Exception:
        status = "failed"
        raise
    finally:
        await publish_chat_event(user_id, status)


@router.post("/chat")
async def chat(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    results = crud.retrieve_chunks(db, body.query, body.top_k)#hybrid vector + full text search, no query parsing needed
    chunks = [
        schemas.RetrieveResult(content=row.content, source=row.source, score=round(score, 6))
        for row, score in results
    ]

    print(f"=== /chat query: '{body.query}' ===")
    for c in chunks:
        print(f"  source={c.source} score={c.score}")
    if not chunks:
        print("  (no chunks retrieved)")
    print("=== end retrieved chunks ===")

    context = build_context(chunks)
    return StreamingResponse(stream_response(body.query, context, current_user.user_id), media_type="text/event-stream")
