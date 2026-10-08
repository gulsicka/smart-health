import dataclasses
from temporalio import activity
import clients.patient.api as patient_client
import clients.provider.api as provider_client
import clients.appointment.api as appointment_client
from notifications import notify_user_appointment
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
    created = (await appointment_client.create_appointment_internal(dataclasses.asdict(appointment))).json()
    # the appointment already exists at this point, so a notification problem must not fail the booking
    try:
        when = f"{appointment.date} from {appointment.start_time[:5]} to {appointment.end_time[:5]}"
        # notifications are stored against user ids, so look up the patient's and provider's user ids
        patient_user_id = (await patient_client.get_patient(appointment.patient_id)).json()["user_id"]
        provider_user_id = (await provider_client.get_provider(appointment.provider_id)).json()["user_id"]
        notify_user_appointment(
            patient_user_id, created["id"], "booking_created",
            f"Appointment {created['id']} has been booked for you on {when}.",
        )
        notify_user_appointment(
            provider_user_id, created["id"], "booking_created",
            f"A new appointment ({created['id']}) has been booked with you on {when}.",
        )
    except Exception as e:
        print(f"Booking notifications skipped: {e}")


@activity.defn
async def notify_booking_failed(data: AppointmentInput):
    message = (
        f"The appointment booking on {data.date} from {data.start_time[:5]} to {data.end_time[:5]} "
        f"could not be confirmed."
    )
    for client_call, entity_id in (
        (patient_client.get_patient, data.patient_id),
        (provider_client.get_provider, data.provider_id),
    ):
        try:
            user_id = (await client_call(entity_id)).json()["user_id"]
        except Exception:
            continue  # the patient/provider may be exactly what failed validation
        notify_user_appointment(user_id, None, "booking_failed", message)
    print(f"Booking failed notification dispatched for patient {data.patient_id}")
