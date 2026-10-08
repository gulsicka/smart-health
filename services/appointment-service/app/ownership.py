import httpx
from fastapi import HTTPException

from app.config import settings
from app.enums import RoleName

STAFF_ROLES = (RoleName.ADMIN, RoleName.FD_STAFF)


def _lookup_id(url: str, token: str) -> int | None:
    # forwards the caller's own token: a patient/provider may read their own profile
    try:
        response = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10.0)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Could not verify record ownership, try again")
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Could not verify record ownership, try again")
    return response.json()["id"]


def ensure_access(current_user, token: str, patient_id: int | None = None, provider_id: int | None = None):
    """Admin and front-desk staff can access any record. A patient or provider can
    only access records that belong to them (matched on the patient/provider profile
    linked to their user id)."""
    roles = current_user.roles
    if any(r in STAFF_ROLES for r in roles):
        return
    if RoleName.PATIENT in roles and patient_id is not None:
        own = _lookup_id(f"{settings.PATIENT_SERVICE_URL}/patients/by-user-id/{current_user.user_id}", token)
        if own is not None and own == patient_id:
            return
    if RoleName.PROVIDER in roles and provider_id is not None:
        own = _lookup_id(f"{settings.PROVIDER_SERVICE_URL}/providers/by-user-id/{current_user.user_id}", token)
        if own is not None and own == provider_id:
            return
    raise HTTPException(status_code=403, detail="You can only access your own records")
