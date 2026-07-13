import os
from temporalio.client import Client

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
PROVIDER_TASK_QUEUE = os.getenv("PROVIDER_TASK_QUEUE", "provider_availability_queue")


async def start_provider_availability_workflow(provider_id: int, body, workflow_id: str):
    client = await Client.connect(TEMPORAL_HOST)
    handle = await client.start_workflow(
        "ProviderAvailabilityWorkflow",
        {
            "provider_id": provider_id,
            "clinic_id": body.clinic_id,
            "working_days": body.working_days,
            "start_time": body.start_time,
            "end_time": body.end_time,
        },
        id=workflow_id,
        task_queue=PROVIDER_TASK_QUEUE,
    )
    return handle
