from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import auth
import crud
import schemas
from database import get_db
from enums import RoleName

router = APIRouter()


@router.get("/notifications/{user_id}", response_model=list[schemas.NotificationOut])
def get_notifications_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    # a caller may always read their own notifications; admin and front-desk
    # staff may look up any user's, the same pattern used elsewhere in the system
    is_staff = RoleName.ADMIN in current_user.roles or RoleName.FD_STAFF in current_user.roles
    if current_user.user_id != user_id and not is_staff:
        raise HTTPException(status_code=403, detail="You can only view your own notifications")

    return crud.get_notifications_by_user(db, user_id)


@router.patch("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    notification = crud.get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # same rule as reading the list: the owner, or admin/front-desk staff, may mark it read
    is_staff = RoleName.ADMIN in current_user.roles or RoleName.FD_STAFF in current_user.roles
    if current_user.user_id != notification.user_id and not is_staff:
        raise HTTPException(status_code=403, detail="You can only update your own notifications")

    return crud.mark_notification_read(db, notification)
