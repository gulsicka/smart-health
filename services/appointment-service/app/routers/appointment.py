from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date as date_type
import uuid

from app.database import get_db
from app import schemas, auth, crud, tasks
from app.utils import workflow_id_for
from app.enums import AppointmentStatus, RoleName
from app import kafka_producer

router = APIRouter()

S = AppointmentStatus

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

ROLE_ALLOWED_TRANSITIONS = {
    S.CONFIRMED:   {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
    S.CHECKED_IN:  {RoleName.ADMIN, RoleName.FD_STAFF},
    S.IN_PROGRESS: {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
    S.COMPLETED:   {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
    S.NO_SHOW:     {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER},
    S.CANCELLED:   {RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER, RoleName.PATIENT},
    S.FAILED:      {RoleName.ADMIN},
}


@router.post("/appointments")
async def create_appointment(
    appointment: schemas.AppointmentCreate,
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PATIENT)),
):
    workflow_id = workflow_id_for(
        f"{appointment.patient_id}-{appointment.provider_id}-{appointment.date}-{appointment.start_time}"
    )
    handle = await tasks.start_appointment_validation_workflow(
        appointment_data={
            "patient_id": appointment.patient_id,
            "provider_id": appointment.provider_id,
            "clinic_id": appointment.clinic_id,
            "department_id": appointment.department_id,
            "date": appointment.date.isoformat(),
            "start_time": appointment.start_time.isoformat(),
            "end_time": appointment.end_time.isoformat(),
            
        },
        workflow_id=workflow_id,
    )
    return {"message": "Appointment request received", "workflow_id": handle.id}


@router.post("/appointments/internal", response_model=schemas.Appointment)
async def create_appointment_internal(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
):
    result = crud.create_appointment_internal(db, appointment)
    await kafka_producer.publish_event(
        event={
            "appointment_id": result.id,
            "patient_id": result.patient_id,
            "provider_id": result.provider_id,
            "clinic_id": result.clinic_id,
            "department_id": result.department_id,
            "date": result.date.isoformat(),
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat(),
            "status": result.status,
            "event_id": str(uuid.uuid4()),
            "event_type": "appointment.created",
            "timestamp": result.created_at.isoformat(),
        },
        key=str(result.id),
    )
    return result


@router.get("/appointments", response_model=list[schemas.Appointment])
def get_appointments(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF)),
):
    return crud.get_all_appointments(db)


@router.get("/appointments/{appointment_id}", response_model=schemas.Appointment)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER)),
):
    appointment = crud.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/appointments/{appointment_id}/status", response_model=schemas.Appointment)
async def update_appointment_status(
    appointment_id: int,
    updates: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(
        auth.require_role(RoleName.ADMIN, RoleName.FD_STAFF, RoleName.PROVIDER, RoleName.PATIENT)
    ),
):
    appointment = crud.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    new_status = updates.status

    allowed_statuses = VALID_TRANSITIONS.get(S(appointment.status), set())
    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{appointment.status}' to '{new_status}'",
        )

    allowed_roles = ROLE_ALLOWED_TRANSITIONS.get(new_status, set())
    if not any(r in allowed_roles for r in current_user.roles):
        raise HTTPException(status_code=403, detail=f"Your role is not allowed to set status to '{new_status}'")

    updated  = crud.update_appointment_status(db, appointment, new_status)
    await kafka_producer.publish_event(
    event={
       "appointment_id": updated.id,
            "patient_id": updated.patient_id,
            "provider_id": updated.provider_id,
            "clinic_id": updated.clinic_id,
            "department_id": updated.department_id,
            "date": updated.date.isoformat(),
            "start_time": updated.start_time.isoformat(),
            "end_time": updated.end_time.isoformat(),
            "status": updated.status,
            "event_id": str(uuid.uuid4()),
            "event_type": "appointment.status_updated",
            "timestamp": updated.created_at.isoformat(),
    },
    key=str(updated.id),
    )
    return updated


@router.get("/providers/{provider_id}/booked-slots", response_model=list[schemas.BookedSlot])
def get_booked_slots(
    provider_id: int,
    date: date_type = Query(..., description="Date to check, e.g. 2026-07-10"),
    clinic_id: int = Query(..., description="Clinic ID"),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    booked = crud.get_booked_slots(db, provider_id, date, clinic_id)
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
    current_user: schemas.TokenData = Depends(auth.require_role(RoleName.ADMIN)),
):
    appointment = crud.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    crud.delete_appointment(db, appointment)
    return {"message": "Appointment deleted"}
