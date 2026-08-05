from temporalio import activity
from schemas import AppointmentReminderInput
import clients.ai.api as ai_client
from notifications import notify_appointment_reminder


@activity.defn
async def send_day_before_reminder(data: AppointmentReminderInput):
    message = await ai_client.generate_reminder(
        appointment_id=data.appointment_id,
        patient_id=data.patient_id,
        provider_id=data.provider_id,
        clinic_id=data.clinic_id,
        date=data.date,
        start_time=data.start_time,
        reminder_type="day_before",
    )
    notify_appointment_reminder(
        patient_id=data.patient_id,
        appointment_id=data.appointment_id,
        message=message,
    )


@activity.defn
async def send_hour_before_reminder(data: AppointmentReminderInput):
    message = await ai_client.generate_reminder(
        appointment_id=data.appointment_id,
        patient_id=data.patient_id,
        provider_id=data.provider_id,
        clinic_id=data.clinic_id,
        date=data.date,
        start_time=data.start_time,
        reminder_type="hour_before",
    )
    notify_appointment_reminder(
        patient_id=data.patient_id,
        appointment_id=data.appointment_id,
        message=message,
    )
