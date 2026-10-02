from sqlalchemy.orm import Session

from app import crud, models, utils
from app.config import settings
from app.database import SessionLocal
from app.enums import RoleName, UserStatus

ALL_ROLES = [r.value for r in RoleName]


def seed_admin() -> None:
    """Ensure the roles table and a default admin user exist.

    Runs on every service startup. Safe to run repeatedly: it only creates
    what's missing, so on an already-seeded database this is a no-op.
    """
    db: Session = SessionLocal()
    try:
        # roles are a prerequisite for assigning a role to the admin user, and
        # nothing else in the system seeds them
        roles_by_name = {}
        for role_name in ALL_ROLES:
            role = crud.get_role_by_name(db, role_name)
            if not role:
                role = crud.create_role(db, role_name)
                print(f"Seeded role: {role_name}")
            roles_by_name[role_name] = role

        admin_email = settings.SYSTEM_EMAIL
        existing = crud.get_user_by_email(db, admin_email)
        if existing:
            return

        admin_user = models.User(
            name="System Admin",
            email=admin_email,
            number=None,
            password_hash=utils.hash_password(settings.SYSTEM_PASSWORD),
            roles=[roles_by_name[RoleName.ADMIN.value]],
            status=UserStatus.ACTIVE.value,
        )
        db.add(admin_user)
        db.commit()
        print(f"Seeded default admin user: {admin_email}")
    finally:
        db.close()
