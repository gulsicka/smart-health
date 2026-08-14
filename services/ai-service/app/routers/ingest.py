from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app import schemas, auth, crud
from app.database import get_db
from app.enums import RoleName
from app.temporal_client import get_temporal_client
from app.config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import base64
import uuid

router = APIRouter()

R = RoleName


@router.post("/ingest", response_model=schemas.IngestResponse)
def ingest(
    body: schemas.IngestRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(body.content)

    crud.delete_chunks(db, body.source)
    crud.ingest_chunks(db, body.source, chunks)
    return schemas.IngestResponse(source=body.source, chunks_stored=len(chunks))


@router.post("/ingest/pdf", response_model=schemas.IngestResponse)
async def ingest_pdf(
    source: str = Form(...),
    file: UploadFile = File(...),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    pdf_bytes = file.file.read()
    pdf_base64 = base64.b64encode(pdf_bytes).decode()

    client = await get_temporal_client()
    workflow_id = f"pdf-ingestion-{source}-{uuid.uuid4()}"
    handle = await client.start_workflow(
        "PdfIngestionWorkflow",
        {"source": source, "pdf_base64": pdf_base64},
        id=workflow_id,
        task_queue=settings.PDF_INGESTION_TASK_QUEUE,
    )
    result = await handle.result()
    message = "Ingestion successful"
    if result["failed_pages"]:
        message = f"Ingestion completed with errors on pages: {result['failed_pages']}"
    return schemas.IngestResponse(source=source, chunks_stored=result["chunks_stored"], message=message)
