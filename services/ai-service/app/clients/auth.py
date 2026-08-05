from app.config import settings
from app.clients.http import make_request

AUTH_SERVICE_URL = settings.AUTH_SERVICE_URL


async def get_user(user_id: int) -> dict:
    response = await make_request("get", f"{AUTH_SERVICE_URL}/users/{user_id}")
    return response.json()


async def get_all_users() -> list:
    response = await make_request("get", f"{AUTH_SERVICE_URL}/users")
    return response.json()
