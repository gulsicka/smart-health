from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app import schemas, auth, crud
from app.database import get_db
from app.enums import RoleName
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz   # pymupdf
import hashlib
from app.clients import provider, patients, appointment
from app.utils.event_text import event_to_text, provider_full_text, patient_full_text, appointment_created_text, clinic_full_text, department_full_text

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
def ingest_pdf(
    source: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    pdf_bytes = file.file.read()
    file_hash = hashlib.md5(pdf_bytes).hexdigest()

    existing = crud.get_existing_chunk(db, source)
    if existing and existing.file_hash == file_hash:
        return schemas.IngestResponse(source=source, chunks_stored=0, message="File unchanged, skipped re-ingestion")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "".join(page.get_text() for page in doc)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    crud.delete_chunks(db, source)
    crud.ingest_chunks(db, source, chunks, file_hash=file_hash)
    return schemas.IngestResponse(source=source, chunks_stored=len(chunks))

@router.post("/ingest/sync", response_model=schemas.SyncResponse)
async def sync(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    counts = {"providers": 0, "patients": 0, "appointments": 0, "clinics": 0, "departments": 0}

    for provider_instance in await provider.get_all_providers():
        crud.delete_chunks(db, f"provider-{provider_instance['id']}")
        crud.ingest_chunks(db, f"provider-{provider_instance['id']}", [provider_full_text(provider_instance)])
        counts["providers"] += 1

    for patient in await patients.get_all_patients():
        crud.delete_chunks(db, f"patient-{patient['id']}")
        crud.ingest_chunks(db, f"patient-{patient['id']}", [patient_full_text(patient)])
        counts["patients"] += 1

    for appt in await appointment.get_all_appointments():
        crud.delete_chunks(db, f"appointment-{appt['id']}")
        crud.ingest_chunks(db, f"appointment-{appt['id']}", [appointment_created_text(appt)])
        counts["appointments"] += 1

    for clinic in await provider.get_all_clinics():
        crud.delete_chunks(db, f"clinic-{clinic['id']}")
        crud.ingest_chunks(db, f"clinic-{clinic['id']}", [clinic_full_text(clinic)])
        counts["clinics"] += 1

    for dept in await provider.get_all_departments():
        crud.delete_chunks(db, f"department-{dept['id']}")
        crud.ingest_chunks(db, f"department-{dept['id']}", [department_full_text(dept)])
        counts["departments"] += 1

    return schemas.SyncResponse(counts=counts)