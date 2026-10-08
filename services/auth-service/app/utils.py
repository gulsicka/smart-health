import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def workflow_id_for(user_id: str) -> str:
    return f"user-creation-{user_id}"

def workflow_id_for_update(user_id: str) -> str:
    return f"user-update-{user_id}"

def root_cause_message(e: BaseException) -> str:
    """Temporal wraps the real error (workflow failure -> activity failure -> the
    exception raised in the activity). Walk down to the innermost one so the caller
    sees the actual reason instead of "Activity task failed"."""
    current = e
    while True:
        inner = getattr(current, "cause", None) or current.__cause__
        if inner is None or inner is current:
            break
        current = inner
    return str(current)
