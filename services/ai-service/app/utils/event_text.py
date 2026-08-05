def provider_deleted_text(event: dict) -> str:
    return (
        f"Provider with ID {event['provider_id']} has been removed from the platform. "
        f"User ID: {event['user_id']}."
    )

def patient_deleted_text(event: dict) -> str:
    return (
        f"Patient with ID {event['patient_id']} has been removed from the platform. "
        f"User ID: {event['user_id']}."
    )


def appointment_created_text(event: dict) -> str:
    # Kafka events use 'appointment_id'; API responses use 'id'
    appt_id = event.get("appointment_id") or event.get("id")
    return (
        f"A new appointment has been booked. "
        f"Appointment ID: {appt_id}. "
        f"Patient ID: {event['patient_id']} with Provider ID: {event['provider_id']} "
        f"at Clinic ID: {event['clinic_id']}. "
        f"Scheduled on {event['date']} from {event['start_time']} to {event['end_time']}. "
        f"Current status: {event['status']}."
    )


def appointment_status_updated_text(event: dict) -> str:
    return (
        f"Appointment ID {event['appointment_id']} status has been updated to {event['status']}. "
        f"Patient ID: {event['patient_id']} with Provider ID: {event['provider_id']} "
        f"at Clinic ID: {event['clinic_id']}. "
        f"Appointment date: {event['date']} from {event['start_time']} to {event['end_time']}."
    )
    
def provider_full_text(provider: dict) -> str:
    # API returns department_id (int), not a nested department object
    return (
        f"Provider ID {provider['id']} is in department ID {provider['department_id']}. "
        f"User ID: {provider['user_id']}. "
        f"Active: {not provider['is_deleted']}."
    )

def patient_full_text(patient: dict) -> str:
    return (
        f"Patient ID {patient['id']} is registered on the platform. "
        f"User ID: {patient['user_id']}."
    )

def clinic_full_text(clinic: dict) -> str:
    dept_names = ", ".join(d['name'] for d in clinic.get('departments', []))
    return (
        f"Clinic '{clinic['name']}' is located at {clinic['address']}. "
        f"Departments offered: {dept_names}."
    )

def department_full_text(dept: dict) -> str:
    return f"Department '{dept['name']}' with ID {dept['id']} is available at SmartHealth."


EVENT_TEXT_MAP = {
    "provider.deleted": provider_deleted_text,
    "patient.deleted": patient_deleted_text,
    "appointment.created": appointment_created_text,
    "appointment.status_updated": appointment_status_updated_text,
}


def event_to_text(event: dict) -> str | None:
    event_type = event.get("event_type")
    converter = EVENT_TEXT_MAP.get(event_type)
    if not converter:
        return None 
    return converter(event)
