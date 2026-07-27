from decimal import Decimal
from sqlalchemy.orm import Session
from app import models
from app.enums import InvoiceStatus


def create_invoice(
    db: Session,
    appointment_id: int,
    patient_id: int,
    provider_id: int,
    clinic_id: int,
    amount: Decimal,
    appointment_date: str | None = None,
) -> models.Invoice:
    invoice = models.Invoice(
        appointment_id=appointment_id,
        patient_id=patient_id,
        provider_id=provider_id,
        clinic_id=clinic_id,
        amount=amount,
        status=InvoiceStatus.PENDING,
        appointment_date=appointment_date,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice_by_id(db: Session, invoice_id: int) -> models.Invoice | None:
    return db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()


def get_invoice_by_appointment(db: Session, appointment_id: int) -> models.Invoice | None:
    return db.query(models.Invoice).filter(models.Invoice.appointment_id == appointment_id).first()


def get_invoices_by_patient(db: Session, patient_id: int) -> list[models.Invoice]:
    return db.query(models.Invoice).filter(models.Invoice.patient_id == patient_id).all()


def get_all_invoices(db: Session) -> list[models.Invoice]:
    return db.query(models.Invoice).all()


def update_invoice_status(db: Session, invoice: models.Invoice, status: InvoiceStatus) -> models.Invoice:
    invoice.status = status
    db.commit()
    db.refresh(invoice)
    return invoice
