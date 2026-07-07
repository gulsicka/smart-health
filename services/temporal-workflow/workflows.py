from temporalio import workflow
from datetime import timedelta
with workflow.unsafe.imports_passed_through():
    #safe to import these modules in the workflow context
    from activities import  (
        create_patient_record,
    )

@workflow.defn
class UserCreationWorkflow:
    @workflow.run
    async def run(self, user_data: dict):
        # call the activity to create a patient record
        print(f"Starting workflow for user: {user_data}")
        if "patient" in user_data["roles"]:
            await workflow.execute_activity(
                create_patient_record,
                user_data,
                start_to_close_timeout=timedelta(seconds=30),
            )
        print("Workflow completed")