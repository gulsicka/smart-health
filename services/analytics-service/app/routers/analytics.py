from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from app.consumer import redis_client
from app.database import SessionLocal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import AppointmentEvent

router = APIRouter()

@router.get("/analytics")
async def get_analytics():

    total_appointments = int((await redis_client.get("analytics:total_appointments")) or 0)
    total_completed = int((await redis_client.get("analytics:total_completed")) or 0)
    total_cancelled = int((await redis_client.get("analytics:total_cancelled")) or 0)
    total_patients = int((await redis_client.get("analytics:total_patients")) or 0)
    daily_bookings = await redis_client.hgetall("analytics:daily_bookings") or {}
    daily_completions = await redis_client.hgetall("analytics:daily_completions") or {}
    daily_cancellations = await redis_client.hgetall("analytics:daily_cancellations") or {}

    total_wait_minutes = float((await redis_client.get("analytics:total_wait_minutes")) or 0)
    wait_time_count = int((await redis_client.get("analytics:wait_time_count")) or 0)
    avg_wait_time_minutes = round(total_wait_minutes / wait_time_count, 2) if wait_time_count else 0

    return {
        "total_appointments": total_appointments,
        "total_completed": total_completed,
        "total_cancelled": total_cancelled,
        "total_patients": total_patients,
        "avg_wait_time_minutes": avg_wait_time_minutes,
        "daily_bookings": daily_bookings,
        "daily_completions": daily_completions,
        "daily_cancellations": daily_cancellations,
        "cancellation_rate": round(total_cancelled / total_appointments, 2) if total_appointments else 0,
    }


@router.get("/analytics/filter")
def get_filtered_analytics(
    from_date: str = Query(...),
    to_date: str = Query(...),
    clinic_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(
        func.time_bucket('1 day', AppointmentEvent.time).label('day'),
        AppointmentEvent.event_type,
        func.count().label('total')
    ).filter(
        AppointmentEvent.time.between(from_date, to_date)
    )

    if clinic_id is not None:
        query = query.filter(AppointmentEvent.clinic_id == clinic_id)

    if provider_id is not None:
        query = query.filter(AppointmentEvent.provider_id == provider_id)

    results = query.group_by('day', AppointmentEvent.event_type).order_by('day').all()

    return [
        {"day": str(row.day.date()), "event_type": row.event_type, "total": row.total}
        for row in results
    ]
    
@router.get("/analytics/total-created")
def get_total_appointments_created(
    from_date: str = Query(...),
    to_date: str = Query(...),
    event_type: str = Query(...),
    db: Session = Depends(get_db),
):
    total = db.query(func.count()).filter(
        AppointmentEvent.time.between(from_date, to_date),
        AppointmentEvent.event_type == event_type
    ).scalar()

    return {"total": total, "event_type": event_type, "from": from_date, "to": to_date}