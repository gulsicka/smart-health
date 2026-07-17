from fastapi import APIRouter
from app.consumer import redis_client


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