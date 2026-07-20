from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.appointment import (
        validate_appointment_entities,
        check_provider_availability,
        check_for_appointment_conflict,
        notify_booking_failed,
    )
    from activities.common import failed_workflow
    from schemas import AppointmentInput, FailedWorkflowInput


@workflow.defn
class AppointmentValidationWorkflow:
    @workflow.run
    async def run(self, appointment_data: AppointmentInput):
        print(f"Starting AppointmentValidationWorkflow: {appointment_data}")
        try:
            await workflow.execute_activity(
                validate_appointment_entities,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            is_available = await workflow.execute_activity(
                check_provider_availability,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            if not is_available:
                raise Exception("Provider is not available for the requested time slot.")

            await workflow.execute_activity(
                check_for_appointment_conflict,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            print("AppointmentValidationWorkflow completed")

        except Exception as e:
            await workflow.execute_activity(
                notify_booking_failed,
                appointment_data,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            await workflow.execute_activity(
                failed_workflow,
                FailedWorkflowInput(error=str(e)),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            raise
