from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.provider import setup_provider_availability
    from activities.common import failed_workflow


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
            print(f"ProviderAvailabilityWorkflow complete: provider={data['provider_id']} clinic={data['clinic_id']}")

        except Exception as e:
            await workflow.execute_activity(
                failed_workflow,
                {"error": str(e), **data},
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            raise
