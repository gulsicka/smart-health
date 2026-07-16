from clients.common.http import make_request
from config import settings

AUTH_URL = settings.AUTH_SERVICE_URL


async def activate_user(user_id: int):
    await make_request("patch", f"{AUTH_URL}/users/{user_id}/activate")


async def delete_user(user_id: int):
    await make_request("delete", f"{AUTH_URL}/users/{user_id}")

async def remove_user_roles(data: dict):
    await make_request(
        "patch",
        f"{AUTH_URL}/users/{data['id']}/remove_roles",
        json={"role_names": data["roles"]},
    )