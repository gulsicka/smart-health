def provider_deleted_text(event: dict, provider_name: str = "Unknown") -> str:
    return (
        f"Provider {provider_name} (ID {event['provider_id']}) has been removed from the platform."
    )


def patient_deleted_text(event: dict, patient_name: str = "Unknown") -> str:
    return (
        f"Patient {patient_name} (ID {event['patient_id']}) has been removed from the platform."
    )


def appointment_created_text(event: dict) -> str:
    # ID-only fallback — used when enriched data is unavailable
    appt_id = event.get("appointment_id") or event.get("id")
    return (
        f"Appointment ID {appt_id} on {event['date']} from {event['start_time']} to {event['end_time']}. "
        f"Status: {event['status']}. "
        f"Patient ID: {event['patient_id']}, Provider ID: {event['provider_id']}, Clinic ID: {event['clinic_id']}."
    )


def appointment_status_updated_text(
    event: dict,
    patient_name: str = "Unknown",
    provider_name: str = "Unknown",
    clinic_name: str = "Unknown",
) -> str:
    return (
        f"Appointment ID {event['appointment_id']} status updated to {event['status']}. "
        f"Patient: {patient_name} (ID {event['patient_id']}). "
        f"Provider: {provider_name} (ID {event['provider_id']}). "
        f"Clinic: {clinic_name} (ID {event['clinic_id']}). "
        f"Date: {event['date']} from {event['start_time']} to {event['end_time']}."
    )


def appointment_full_text(
    appt: dict,
    patient_name: str,
    provider_name: str,
    department_name: str,
    clinic: dict,
) -> str:
    appt_id = appt.get("appointment_id") or appt.get("id")
    clinic_name = clinic.get("name", "Unknown")
    clinic_address = clinic.get("address", "Unknown")
    return (
        f"Appointment ID {appt_id} on {appt['date']} from {appt['start_time']} to {appt['end_time']}. "
        f"Status: {appt['status']}. "
        f"Patient: {patient_name} (ID {appt['patient_id']}). "
        f"Provider: {provider_name} (ID {appt['provider_id']}). "
        f"Department: {department_name}. "
        f"Clinic: {clinic_name} at {clinic_address} (ID {appt['clinic_id']})."
    )


def provider_full_text(provider: dict, user: dict, department: dict) -> str:
    return (
        f"Provider: {user.get('name', 'Unknown')} (ID {provider['id']}). "
        f"Email: {user.get('email', 'N/A')}. "
        f"Phone: {user.get('number') or 'N/A'}. "
        f"Department: {department.get('name', 'Unknown')} (ID {provider['department_id']}). "
        f"Status: {'Active' if not provider['is_deleted'] else 'Deleted'}."
    )


def patient_full_text(patient: dict, user: dict) -> str:
    dob = patient.get("date_of_birth", "Unknown")
    return (
        f"Patient: {user.get('name', 'Unknown')} (ID {patient['id']}). "
        f"Email: {user.get('email', 'N/A')}. "
        f"Phone: {user.get('number') or 'N/A'}. "
        f"Date of Birth: {dob}. "
        f"Status: {'Active' if not patient['is_deleted'] else 'Deleted'}."
    )


def clinic_full_text(clinic: dict) -> str:
    dept_names = ", ".join(d["name"] for d in clinic.get("departments", []))
    return (
        f"Clinic: {clinic['name']} (ID {clinic['id']}) at {clinic['address']}. "
        f"Departments: {dept_names or 'None'}."
    )


def department_full_text(dept: dict) -> str:
    return f"Department: {dept['name']} (ID {dept['id']})."


# used only for truly unknown event types that fall through in kafka_consumer
EVENT_TEXT_MAP = {
    "appointment.created": appointment_created_text,
}


def event_to_text(event: dict) -> str | None:
    event_type = event.get("event_type")
    converter = EVENT_TEXT_MAP.get(event_type)
    if not converter:
        return None
    return converter(event)
