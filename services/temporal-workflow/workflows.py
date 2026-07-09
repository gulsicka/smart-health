from temporalio import workflow
from datetime import timedelta
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    #safe to import these modules in the workflow context
    from activities import  (
        create_patient_record,
        create_provider_record,
        validate_appointment_entities,
        check_provider_availability,
        check_for_appointment_conflict,
        failed_workflow,
        setup_provider_availability,
    )

@workflow.defn
class UserCreationWorkflow:
    @workflow.run
    async def run(self, user_data: dict):
        # call the activity to create a patient record
        print(f"Starting workflow for user: {user_data}")

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
            
            print("Workflow completed")
        except Exception as e:
            await workflow.execute_activity(
                failed_workflow,
                {"error": str(e), **user_data},
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            raise  # marks workflow as failed in Temporal UI
        
@workflow.defn
class ProviderAvailabilityWorkflow:
    @workflow.run
    async def run(self, data: dict):
        try:
            await workflow.execute_activity(
                setup_provider_availability,
                data,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            print(f"Provider availability setup complete for provider {data['provider_id']} at clinic {data['clinic_id']}")
        except Exception as e:
            await workflow.execute_activity(
                failed_workflow,
                {"error": str(e), **data},
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            raise


@workflow.defn
class AppointmentValidationWorkflow:
    @workflow.run
    async def run(self, appointment_data: dict):
        try:
            print(f"Starting appointment validation workflow for data: {appointment_data}")

            # call the activity to validate the entities
            await workflow.execute_activity(
                validate_appointment_entities,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

            # call the activity to check provider availability
            is_available = await workflow.execute_activity(
                check_provider_availability,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2), 
            )
            
            if not is_available:
                raise Exception("Provider is not available for the requested time slot.")

            await workflow.execute_activity(
                check_for_appointment_conflict,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            print("Appointment validation workflow completed successfully.")
        except Exception as e:
            await workflow.execute_activity(
                failed_workflow,
                {"error": str(e), **appointment_data},
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            raise  # marks workflow as failed in Temporal UI