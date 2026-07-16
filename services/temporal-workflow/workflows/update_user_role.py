from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.user import (
        create_patient_record,
        create_provider_record,
        remove_user_role_on_failure
    )
    


@workflow.defn
class UpdateUserWorkflow:
    @workflow.run
    async def run(self, user_data: dict):
        print(f"Starting UpdateUserWorkflow for user: {user_data['id']}")
        
        try:
            if "patient" in user_data["roles"]:
                await workflow.execute_activity(
                    create_patient_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )

            if "provider" in user_data["roles"]:
                await workflow.execute_activity(
                    create_provider_record,
                    user_data,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )

            print("UpdateUserWorkflow completed")
        except Exception as e:
            print(f"UpdateUserWorkflow failed for user: {user_data['id']}, error: {e}")
            # remove new roles if any of the activities fail
            await workflow.execute_activity(
                remove_user_role_on_failure,
                user_data,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
                
            raise