from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app import schemas, auth, embedder, models
from app.database import get_db
from app.enums import RoleName
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz   # pymupdf
import hashlib

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

    db.query(models.DocumentChunk).filter(models.DocumentChunk.source == body.source).delete()
    for chunk in chunks:
        db.add(models.DocumentChunk(
            source=body.source,
            content=chunk,
            embedding=embedder.embed(chunk),
        ))
    db.commit()
    return schemas.IngestResponse(source=body.source, chunks_stored=len(chunks))


@router.post("/ingest/pdf", response_model=schemas.IngestResponse)
def ingest_pdf(
    source: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    pdf_bytes = file.file.read()
    file_hash = hashlib.md5(pdf_bytes).hexdigest()  # hash to detect unchanged files

    existing = db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source).first()
    if existing and existing.file_hash == file_hash:
        return schemas.IngestResponse(source=source, chunks_stored=0, message="File unchanged, skipped re-ingestion")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "".join(page.get_text() for page in doc)  # join all pages into one string

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source).delete()
    for chunk in chunks:
        db.add(models.DocumentChunk(
            source=source,
            content=chunk,
            embedding=embedder.embed(chunk),
            file_hash=file_hash,
        ))
    db.commit()
    return schemas.IngestResponse(source=source, chunks_stored=len(chunks))
