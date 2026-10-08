from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud, auth
from app.enums import RoleName
from app.ownership import ensure_access
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()


@router.get("/invoices", tags=["Invoices"], response_model=list[schemas.InvoiceOut])
def get_all_invoices(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF)),
):
    return crud.get_all_invoices(db)


@router.get("/invoices/{invoice_id}", tags=["Invoices"], response_model=schemas.InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER)
    ),
    credentials: HTTPAuthorizationCredentials = Depends(auth.bearer_scheme),
):
    invoice = crud.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    ensure_access(current_user, credentials.credentials, provider_id=invoice.provider_id)
    return invoice


@router.get("/invoices/appointment/{appointment_id}", tags=["Invoices"], response_model=schemas.InvoiceOut)
def get_invoice_by_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER)
    ),
    credentials: HTTPAuthorizationCredentials = Depends(auth.bearer_scheme),
):
    invoice = crud.get_invoice_by_appointment(db, appointment_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    ensure_access(current_user, credentials.credentials, provider_id=invoice.provider_id)
    return invoice


@router.get("/invoices/patient/{patient_id}", tags=["Invoices"], response_model=list[schemas.InvoiceOut])
def get_invoices_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PATIENT)
    ),
    credentials: HTTPAuthorizationCredentials = Depends(auth.bearer_scheme),
):
    ensure_access(current_user, credentials.credentials, patient_id=patient_id)
    return crud.get_invoices_by_patient(db, patient_id)


@router.get("/invoices/provider/{provider_id}", tags=["Invoices"], response_model=list[schemas.InvoiceOut])
def get_invoices_by_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER)
    ),
    credentials: HTTPAuthorizationCredentials = Depends(auth.bearer_scheme),
):
    ensure_access(current_user, credentials.credentials, provider_id=provider_id)
    return crud.get_invoices_by_provider(db, provider_id)
