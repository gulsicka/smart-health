from datetime import datetime, timedelta

import httpx
from jose import jwt

from .config import settings


def _service_headers() -> dict:
    # short-lived internal admin token, signed with the shared secret, so this
    # service can read patient/provider records the same way a logged-in admin would
    token = jwt.encode(
        {"user_id": 0, "roles": ["admin"], "exp": datetime.utcnow() + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


async def _fetch_user_id(url: str) -> int | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=_service_headers())
            response.raise_for_status()
            return response.json()["user_id"]
    except Exception as e:
        print(f"User lookup failed for {url}: {e}")
        return None


async def get_patient_user_id(patient_id: int) -> int | None:
    return await _fetch_user_id(f"{settings.PATIENT_SERVICE_URL}/patients/{patient_id}")


async def get_provider_user_id(provider_id: int) -> int | None:
    return await _fetch_user_id(f"{settings.PROVIDER_SERVICE_URL}/providers/{provider_id}")
