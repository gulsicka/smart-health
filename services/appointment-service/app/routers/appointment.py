from fastapi import APIRouter, Depends, HTTPException, Query
from temporalio.client import Client
from app.utils import workflow_id_for
import os
from sqlalchemy.orm import Session
from datetime import date as date_type
from app.database import get_db
from app import models, schemas, oauth
from app.enums import AppointmentStatus, RoleName

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")

router = APIRouter()

S = AppointmentStatus  # shorthand

VALID_TRANSITIONS = {
    S.REQUESTED:   {S.CONFIRMED, S.CANCELLED, S.FAILED},
    S.CONFIRMED:   {S.CHECKED_IN, S.CANCELLED, S.NO_SHOW},
    S.CHECKED_IN:  {S.IN_PROGRESS, S.CANCELLED},
    S.IN_PROGRESS: {S.COMPLETED, S.CANCELLED},
    S.COMPLETED:   set(),
    S.NO_SHOW:     set(),
    S.CANCELLED:   set(),
    S.FAILED:      set(),
}


@router.post("/appointments")
async def create_appointment(
    appointment: schemas.AppointmentCreate,
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PATIENT))
):
    
    client = await Client.connect(TEMPORAL_HOST)
    
    workflow_id = workflow_id_for(f"{appointment.patient_id}-{appointment.provider_id}-{appointment.date}-{appointment.start_time}") # same patient cant nook an appointment with same provider at same time
    
    handle = await client.start_workflow(
        "AppointmentValidationWorkflow",
        {
            "patient_id": appointment.patient_id,
            "provider_id": appointment.provider_id,
            "clinic_id": appointment.clinic_id,
            "department_id": appointment.department_id,
            "date": appointment.date.isoformat(),
            "start_time": appointment.start_time.isoformat(),
            "end_time": appointment.end_time.isoformat(),
        },
        id=workflow_id,
        task_queue=os.getenv("APPOINTMENT_TASK_QUEUE", "appointment_validation_queue"),
    )
    
    return {"message": "Appointment request received", "workflow_id": handle.id}

@router.post("/appointments/internal", response_model=schemas.Appointment)
def create_appointment_internal(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db)
):
    db_appointment = models.Appointment(
        **appointment.model_dump(),
        status=S.CONFIRMED,  # already validated, goes straight to confirmed
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@router.get("/appointments", response_model=list[schemas.Appointment])
def get_appointments(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN, RoleName.FD_STAFF))
):
    return db.query(models.Appointment).all()


@router.get("/appointments/{appointment_id}", response_model=schemas.Appointment)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER))
):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/appointments/{appointment_id}/status", response_model=schemas.Appointment)
def update_appointment_status(
    appointment_id: int,
    updates: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER, RoleName.PATIENT))
):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    new_status = updates.status  # already validated by Pydantic as AppointmentStatus

    # Check the status transition is valid
    allowed = VALID_TRANSITIONS.get(S(appointment.status), set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{appointment.status}' to '{new_status}'"
        )

    # Check the user's role is allowed to perform this specific transition
    ROLE_ALLOWED_TRANSITIONS = {
        S.CONFIRMED:   {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
        S.CHECKED_IN:  {RoleName.ADMIN, RoleName.FD_STAFF},
        S.IN_PROGRESS: {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
        S.COMPLETED:   {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
        S.NO_SHOW:     {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
        S.CANCELLED:   {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER, RoleName.PATIENT},
        S.FAILED:      {RoleName.ADMIN},
    }
    allowed_roles = ROLE_ALLOWED_TRANSITIONS.get(new_status, set())
    if not any(r in allowed_roles for r in current_user.roles):
        raise HTTPException(status_code=403, detail=f"Your role is not allowed to set status to '{new_status}'")

    appointment.status = new_status
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/providers/{provider_id}/booked-slots", response_model=list[schemas.BookedSlot])
def get_booked_slots(
    provider_id: int,
    date: date_type = Query(..., description="Date to check, e.g. 2026-07-10"),
    clinic_id: int = Query(..., description="Clinic ID"),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.get_current_user)
):
    """
    Returns all booked (non-cancellable) time slots for a provider on a given date at a clinic.
    The frontend subtracts these from the provider's availability window to show free slots —
    same as how Google Calendar shows busy times for meeting invitees.
    """
    booked = db.query(models.Appointment).filter(
        models.Appointment.provider_id == provider_id,
        models.Appointment.date == date,
        models.Appointment.clinic_id == clinic_id,
        models.Appointment.status.in_([S.REQUESTED, S.CONFIRMED, S.CHECKED_IN, S.IN_PROGRESS]),
    ).all()

    return [
        schemas.BookedSlot(
            appointment_id=a.id,
            start_time=a.start_time,
            end_time=a.end_time,
            status=a.status,
        )
        for a in booked
    ]


@router.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth.require_role(RoleName.ADMIN))
):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appointment)
    db.commit()
    return {"message": "Appointment deleted"}
