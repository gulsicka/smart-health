import dataclasses
from temporalio import activity
import clients.patient.api as patient_client
import clients.provider.api as provider_client
import clients.appointment.api as appointment_client
from notifications import notify_booking_created, notify_booking_failed as _dispatch_booking_failed
from schemas import AppointmentInput


@activity.defn
async def validate_appointment_entities(data: AppointmentInput):
    await patient_client.get_patient(data.patient_id)
    await provider_client.get_provider(data.provider_id)
    # await provider_client.get_department(data.department_id)
    await provider_client.get_clinic(data.clinic_id)


@activity.defn
async def check_provider_availability(data: AppointmentInput):
    response = await provider_client.get_provider_availability(data.provider_id)
    availability_list = response.json()
    appt_start = data.start_time[:5]
    appt_end = data.end_time[:5]
    for avail in availability_list:
        if avail.get("clinic_id") != data.clinic_id:
            continue
        for slot in avail.get("schedule", []):
            if (
                slot.get("date") == data.date
                and slot.get("status") == "available"
                and slot.get("start_time") <= appt_start
                and slot.get("end_time") >= appt_end
            ):
                return True
    raise Exception("Provider is not available at the requested time.")


@activity.defn
async def check_for_appointment_conflict(appointment: AppointmentInput):
    response = await appointment_client.get_appointments()
    appointments = response.json()
    for appt in appointments:
        if (
            appt["provider_id"] == appointment.provider_id
            and appt["date"] == appointment.date
            and appt["status"] in ["requested", "confirmed", "checked_in", "in_progress"]
            and appt["start_time"] < appointment.end_time
            and appt["end_time"] > appointment.start_time
        ):
            raise Exception("Provider already has an appointment in this time slot.")
    await appointment_client.create_appointment_internal(dataclasses.asdict(appointment))
    notify_booking_created(
        patient_id=appointment.patient_id,
        provider_id=appointment.provider_id,
        date=appointment.date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
    )


@activity.defn
async def notify_booking_failed(data: AppointmentInput):
    _dispatch_booking_failed(
        patient_id=data.patient_id,
        provider_id=data.provider_id,
        clinic_id=data.clinic_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    print(f"Booking failed notification dispatched for patient {data.patient_id}")
