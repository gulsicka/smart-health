def workflow_id_for(appointment_id: str) -> str:
    return f"appoinmtent-creation-{appointment_id}"

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
