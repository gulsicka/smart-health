from pydantic import BaseModel
from app.enums import RoleName, CommunicationType


class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


class IngestRequest(BaseModel):
    source: str          # identifier for what this content is (e.g. "provider-schedules", "clinic-faq")
    content: str         # raw text to chunk and embed


class IngestResponse(BaseModel):
    source: str
    chunks_stored: int
    message: str = "Ingestion successful"


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5


class RetrieveResult(BaseModel):
    content: str
    source: str
    score: float


class RetrieveResponse(BaseModel):
    results: list[RetrieveResult]

class SyncResponse(BaseModel):
    counts: dict

class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    
class Communication(BaseModel):
    type: CommunicationType
