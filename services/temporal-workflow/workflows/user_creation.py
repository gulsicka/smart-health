from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.user_creation import (
        create_patient_record,
        create_provider_record,
        activate_user,
        fail_user,
        delete_patient_record,
    )


@workflow.defn
class UserCreationWorkflow:
    @workflow.run
    async def run(self, user_data: dict):
        print(f"Starting UserCreationWorkflow for user: {user_data['id']}")
        patient_created = False

        try:
            if "patient" in user_data["roles"]:
                await workflow.execute_activity(
                    create_patient_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                patient_created = True

            if "provider" in user_data["roles"]:
                await workflow.execute_activity(
                    create_provider_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )

            await workflow.execute_activity(
                activate_user,
                {"user_id": user_data["id"]},
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=10),
            )
            print("UserCreationWorkflow completed")

        except Exception:
            if patient_created:
                await workflow.execute_activity(
                    delete_patient_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=10),
                )
            await workflow.execute_activity(
                fail_user,
                {"user_id": user_data["id"]},
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=10),
            )
            raise
