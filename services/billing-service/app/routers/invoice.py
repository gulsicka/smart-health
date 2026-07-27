from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud, auth
from app.enums import RoleName

router = APIRouter()


@router.get("/invoices", response_model=list[schemas.InvoiceOut])
def get_all_invoices(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF)),
):
    return crud.get_all_invoices(db)


@router.get("/invoices/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF)),
):
    invoice = crud.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/invoices/appointment/{appointment_id}", response_model=schemas.InvoiceOut)
def get_invoice_by_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER)
    ),
):
    invoice = crud.get_invoice_by_appointment(db, appointment_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/invoices/patient/{patient_id}", response_model=list[schemas.InvoiceOut])
def get_invoices_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PATIENT)
    ),
):
    return crud.get_invoices_by_patient(db, patient_id)
