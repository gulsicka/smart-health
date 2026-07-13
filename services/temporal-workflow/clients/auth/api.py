import os
from clients.common.http import make_request

AUTH_URL = os.getenv("AUTH_SERVICE_URL")


async def activate_user(user_id: int):
    await make_request("patch", f"{AUTH_URL}/users/{user_id}/activate")


async def delete_user(user_id: int):
    await make_request("delete", f"{AUTH_URL}/users/{user_id}")
