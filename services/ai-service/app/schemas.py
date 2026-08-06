from pydantic import BaseModel
from app.enums import RoleName, CommunicationType, ReportType


class TokenData(BaseModel):
    user_id: int
    roles: list[RoleName]


class IngestRequest(BaseModel):
    source: str
    content: str


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
    
class GenerateCommunicationRequest(BaseModel):
    type: CommunicationType
    top_k: int = 5
    patient_id: int | None = None
    provider_id: int | None = None
    clinic_id: int | None = None
    
class GenerateCommunicationResponse(BaseModel):
    content: str


class GenerateReminderRequest(BaseModel):
    appointment_id: int
    patient_id: int
    provider_id: int
    clinic_id: int
    date: str
    start_time: str
    reminder_type: str


class GenerateReminderResponse(BaseModel):
    content: str
    
class GenerateReportRequest(BaseModel):
    report_type: ReportType
    date: str | None = None


class GenerateReportResponse(BaseModel):
    content: str