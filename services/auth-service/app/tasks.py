import os
from temporalio.client import Client

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TASK_QUEUE = os.getenv("USER_TASK_QUEUE")


async def start_user_creation_workflow(user_data: dict, workflow_id: str):
    client = await Client.connect(TEMPORAL_HOST)
    handle = await client.start_workflow(
        "UserCreationWorkflow",
        user_data,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    return handle
