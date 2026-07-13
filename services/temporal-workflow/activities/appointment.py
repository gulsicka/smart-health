from temporalio import activity
import clients.patient.api as patient_client
import clients.provider.api as provider_client
import clients.appointment.api as appointment_client


@activity.defn
async def validate_appointment_entities(data: dict):
    await patient_client.get_patient(data["patient_id"])
    await provider_client.get_provider(data["provider_id"])
    await provider_client.get_department(data["department_id"])
    await provider_client.get_clinic(data["clinic_id"])


@activity.defn
async def check_provider_availability(data: dict):
    response = await provider_client.get_provider_availability(data["provider_id"])
    availability_list = response.json()
    for avail in availability_list:
        if (
            avail["date"] == data["date"]
            and avail["start_time"] <= data["start_time"]
            and avail["end_time"] >= data["end_time"]
        ):
            return True
    raise Exception("Provider is not available at the requested time.")


@activity.defn
async def check_for_appointment_conflict(appointment: dict):
    response = await appointment_client.get_appointments()
    appointments = response.json()
    for appt in appointments:
        if (
            appt["provider_id"] == appointment["provider_id"]
            and appt["date"] == appointment["date"]
            and appt["status"] in ["requested", "confirmed", "checked_in", "in_progress"]
            and appt["start_time"] < appointment["end_time"]
            and appt["end_time"] > appointment["start_time"]
        ):
            raise Exception("Provider already has an appointment in this time slot.")
    await appointment_client.create_appointment_internal(appointment)
