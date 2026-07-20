from temporalio import activity
import clients.auth.api as auth_client
import clients.patient.api as patient_client
import clients.provider.api as provider_client
from notifications import notify_user_created as _dispatch_user_created
from notifications import notify_user_creation_failed as _dispatch_user_creation_failed
from notifications import notify_user_role_updated as _dispatch_role_updated
from notifications import notify_user_role_update_failed as _dispatch_role_update_failed
from schemas import UserInput, UserIdInput, NotifyUserInput


@activity.defn
async def create_patient_record(user_data: UserInput):
    await patient_client.create_patient(
        user_id=user_data.id,
        date_of_birth=user_data.date_of_birth,
    )


@activity.defn
async def create_provider_record(user_data: UserInput):
    await provider_client.create_provider(
        user_id=user_data.id,
        department_id=user_data.department_id,
    )


@activity.defn
async def activate_user(data: UserIdInput):
    await auth_client.activate_user(user_id=data.user_id)


@activity.defn
async def fail_user(data: UserIdInput):
    await auth_client.delete_user(user_id=data.user_id)


@activity.defn
async def delete_patient_record(data: UserIdInput):
    await patient_client.delete_patient_by_user_id(user_id=data.user_id)


@activity.defn
async def delete_provider_record(data: UserIdInput):
    await provider_client.delete_provider_by_user_id(user_id=data.user_id)


@activity.defn
async def remove_user_role_on_failure(data: UserInput):
    await auth_client.remove_user_roles(data)


@activity.defn
async def notify_user_created_activity(data: NotifyUserInput):
    _dispatch_user_created(user_id=data.user_id, roles=data.roles)


@activity.defn
async def notify_user_creation_failed_activity(data: UserIdInput):
    _dispatch_user_creation_failed(user_id=data.user_id)


@activity.defn
async def notify_user_role_updated_activity(data: NotifyUserInput):
    _dispatch_role_updated(user_id=data.user_id, roles=data.roles)


@activity.defn
async def notify_user_role_update_failed_activity(data: NotifyUserInput):
    _dispatch_role_update_failed(user_id=data.user_id, roles=data.roles)
