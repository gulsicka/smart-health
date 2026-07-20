from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.user import (
        create_patient_record,
        create_provider_record,
        activate_user,
        fail_user,
        delete_patient_record,
        delete_provider_record,
        notify_user_created_activity,
        notify_user_creation_failed_activity,
    )
    from schemas import UserInput, UserIdInput, NotifyUserInput


@workflow.defn
class UserCreationWorkflow:
    @workflow.run
    async def run(self, user_data: UserInput):
        print(f"Starting UserCreationWorkflow for user: {user_data.id}")
        patient_created = False
        provider_created = False

        try:
            if "patient" in user_data.roles:
                await workflow.execute_activity(
                    create_patient_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                patient_created = True

            if "provider" in user_data.roles:
                await workflow.execute_activity(
                    create_provider_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                provider_created = True

            await workflow.execute_activity(
                activate_user,
                UserIdInput(user_id=user_data.id),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # notification failure does not warrant rollback — user is active in DB
            try:
                await workflow.execute_activity(
                    notify_user_created_activity,
                    NotifyUserInput(user_id=user_data.id, roles=user_data.roles),
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=5),
                )
            except Exception:
                print(f"notify_user_created failed for user {user_data.id}, continuing")

            print("UserCreationWorkflow completed")

        except Exception:
            # rollback order: provider → patient → user
            if provider_created:
                await workflow.execute_activity(
                    delete_provider_record,
                    UserIdInput(user_id=user_data.id),
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=10),
                )
            if patient_created:
                await workflow.execute_activity(
                    delete_patient_record,
                    UserIdInput(user_id=user_data.id),
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=10),
                )
            await workflow.execute_activity(
                fail_user,
                UserIdInput(user_id=user_data.id),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=10),
            )
            try:
                await workflow.execute_activity(
                    notify_user_creation_failed_activity,
                    UserIdInput(user_id=user_data.id),
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=5),
                )
            except Exception:
                print(f"notify_user_creation_failed dispatch failed for user {user_data.id}, continuing")
            raise
