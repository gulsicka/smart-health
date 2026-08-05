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

router = APIRouter()

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    streaming=True,
)

SYSTEM_PROMPT = """You are a helpful assistant for SmartHealth, a healthcare management platform.
Answer the user's question using only the context provided below.
If the context does not contain enough information, say so honestly.

Context:
{context}"""


async def stream_response(query: str, context: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{query}"),
    ])
    chain = prompt | llm
    async for chunk in chain.astream({"context": context, "query": query}):
        if chunk.content:
            yield f"data: {chunk.content}\n\n"


@router.post("/chat")
async def chat(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    results = crud.retrieve_chunks(db, body.query, body.top_k)
    chunks = [
        schemas.RetrieveResult(content=row.content, source=row.source, score=round(score, 6))
        for row, score in results
    ]
    context = build_context(chunks)
    return StreamingResponse(stream_response(body.query, context), media_type="text/event-stream")
