import httpx
from app.config import settings

_token = None


async def get_service_token():
    global _token
    if _token:
        return _token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/login",
            json={"email": settings.SYSTEM_EMAIL, "password": settings.SYSTEM_PASSWORD},
        )
        response.raise_for_status()
        _token = response.json()["access_token"]
    return _token


async def make_request(method: str, url: str, **kwargs):
    """Authenticated HTTP request with automatic token refresh on 401."""
    global _token
    token = await get_service_token()

    async with httpx.AsyncClient() as client:
        response = await getattr(client, method)(
            url,
            headers={"Authorization": f"Bearer {token}"},
            **kwargs,
        )

        if response.status_code == 401:
            _token = None
            token = await get_service_token()
            response = await getattr(client, method)(
                url,
                headers={"Authorization": f"Bearer {token}"},
                **kwargs,
            )

        response.raise_for_status()
        return response
