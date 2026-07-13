from temporalio import activity
import clients.auth.api as auth_client
import clients.patient.api as patient_client
import clients.provider.api as provider_client


@activity.defn
async def create_patient_record(user_data: dict):
    await patient_client.create_patient(
        user_id=user_data["id"],
        date_of_birth=user_data["date_of_birth"],
    )


@activity.defn
async def create_provider_record(user_data: dict):
    await provider_client.create_provider(
        user_id=user_data["id"],
        department_id=user_data.get("department_id"),
    )


@activity.defn
async def activate_user(data: dict):
    await auth_client.activate_user(user_id=data["user_id"])


@activity.defn
async def fail_user(data: dict):
    await auth_client.delete_user(user_id=data["user_id"])


@activity.defn
async def delete_patient_record(data: dict):
    await patient_client.delete_patient_by_user_id(user_id=data["id"])
