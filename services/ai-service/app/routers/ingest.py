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
from app.clients import provider as provider_client, patients as patients_client
from app.clients import auth as auth_client
from app.clients import appointment as appointment_client
from app.utils.event_text import (
    patient_full_text,
    provider_full_text,
    appointment_full_text,
    clinic_full_text,
    department_full_text,
)
from app.utils import report_text
from datetime import date

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


@router.post("/ingest/sync", response_model=schemas.SyncResponse)
async def sync(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(R.ADMIN)),
):
    counts = {"providers": 0, "patients": 0, "appointments": 0, "clinics": 0, "departments": 0, "report_chunks": 0}

    # build lookup maps upfront — one call per service, no N+1
    all_users = await auth_client.get_all_users()
    user_map = {u["id"]: u for u in all_users}

    all_depts = await provider_client.get_all_departments()
    dept_map = {d["id"]: d for d in all_depts}

    all_clinics = await provider_client.get_all_clinics()
    clinic_map = {c["id"]: c for c in all_clinics}

    all_patients = await patients_client.get_all_patients()
    patient_map = {p["id"]: p for p in all_patients}

    all_providers = await provider_client.get_all_providers()
    provider_map = {p["id"]: p for p in all_providers}

    for prov in all_providers:
        user = user_map.get(prov["user_id"], {})
        dept = dept_map.get(prov["department_id"], {"name": "Unknown", "id": prov["department_id"]})
        crud.delete_chunks(db, f"provider-{prov['id']}")
        crud.ingest_chunks(db, f"provider-{prov['id']}", [provider_full_text(prov, user, dept)])
        counts["providers"] += 1

    for patient in all_patients:
        user = user_map.get(patient["user_id"], {})
        crud.delete_chunks(db, f"patient-{patient['id']}")
        crud.ingest_chunks(db, f"patient-{patient['id']}", [patient_full_text(patient, user)])
        counts["patients"] += 1

    all_appointments = await appointment_client.get_all_appointments()

    for appt in all_appointments:
        patient = patient_map.get(appt["patient_id"], {})
        patient_user = user_map.get(patient.get("user_id"), {})
        prov = provider_map.get(appt["provider_id"], {})
        provider_user = user_map.get(prov.get("user_id"), {})
        dept = dept_map.get(prov.get("department_id"), {"name": "Unknown"})
        clinic = clinic_map.get(appt["clinic_id"], {"name": "Unknown", "address": "Unknown"})
        source = f"patient-{appt['patient_id']}-provider-{appt['provider_id']}-clinic-{appt['clinic_id']}-appointment-{appt['id']}"
        text = appointment_full_text(
            appt,
            patient_user.get("name", "Unknown"),
            provider_user.get("name", "Unknown"),
            dept.get("name", "Unknown"),
            clinic,
        )
        crud.delete_chunks(db, source)
        crud.ingest_chunks(db, source, [text])
        counts["appointments"] += 1

    for clinic in all_clinics:
        crud.delete_chunks(db, f"clinic-{clinic['id']}")
        crud.ingest_chunks(db, f"clinic-{clinic['id']}", [clinic_full_text(clinic)])
        counts["clinics"] += 1

    for dept in all_depts:
        crud.delete_chunks(db, f"department-{dept['id']}")
        crud.ingest_chunks(db, f"department-{dept['id']}", [department_full_text(dept)])
        counts["departments"] += 1

    # ---- report stat chunks — precomputed here so /generate/report is a plain, deterministic
    # chunk lookup (exact source match, no similarity search) instead of live microservice calls ----
    distinct_dates = sorted({str(a["date"])[:10] for a in all_appointments})
    today_str = date.today().isoformat()
    if today_str not in distinct_dates:
        distinct_dates.append(today_str)

    for date_str in distinct_dates:
        stats_text, records_text = report_text.build_daily_report(
            date_str, all_appointments, all_providers, all_depts, all_clinics, all_patients,
            provider_map, dept_map, user_map,
        )
        stats_source = f"report-daily_appointments-{date_str}"
        crud.delete_chunks(db, stats_source)
        crud.ingest_chunks(db, stats_source, [stats_text])
        counts["report_chunks"] += 1

        records_source = f"report-daily_appointments-{date_str}-records"
        crud.delete_chunks(db, records_source)
        crud.ingest_chunks(db, records_source, [records_text])
        counts["report_chunks"] += 1

        exec_text = report_text.build_executive_snapshot(
            date_str, all_appointments, all_providers, all_depts, all_clinics, all_patients,
            provider_map, dept_map,
        )
        exec_source = f"report-executive_snapshot-{date_str}"
        crud.delete_chunks(db, exec_source)
        crud.ingest_chunks(db, exec_source, [exec_text])
        counts["report_chunks"] += 1

    dept_util_text = report_text.build_department_utilization(all_appointments, all_depts, provider_map, user_map)
    crud.delete_chunks(db, "report-department_utilization")
    crud.ingest_chunks(db, "report-department_utilization", [dept_util_text])
    counts["report_chunks"] += 1

    engagement_text = report_text.build_patient_engagement(all_appointments, all_patients, user_map)
    crud.delete_chunks(db, "report-patient_engagement")
    crud.ingest_chunks(db, "report-patient_engagement", [engagement_text])
    counts["report_chunks"] += 1

    return schemas.SyncResponse(counts=counts)
