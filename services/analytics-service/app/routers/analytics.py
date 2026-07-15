from fastapi import APIRouter
from app.consumer import redis_client


router = APIRouter()

@router.get("/analytics")
async def get_analytics():
    # Placeholder for analytics logic
    
    total_appointments = int((await redis_client.get("analytics:total_appointments")) or 0)
    total_completed = int((await redis_client.get("analytics:total_completed")) or 0)
    total_cancelled = int((await redis_client.get("analytics:total_cancelled")) or 0)
    daily_bookings = await redis_client.hgetall("analytics:daily_bookings") or {}
    daily_completions = await redis_client.hgetall("analytics:daily_completions") or {}
    daily_cancellations = await redis_client.hgetall("analytics:daily_cancellations") or {}

    return {
        "total_appointments": total_appointments,
        "total_completed": total_completed,
        "total_cancelled": total_cancelled,
        "daily_bookings": daily_bookings,
        "daily_completions": daily_completions,
        "daily_cancellations": daily_cancellations,
        "cancellation_rate": round(total_cancelled / total_appointments, 2) if total_appointments else 0,
    }