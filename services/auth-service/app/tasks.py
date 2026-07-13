from temporalio.client import Client
from app.config import settings


async def start_user_creation_workflow(user_data: dict, workflow_id: str):
    client = await Client.connect(settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE)
    handle = await client.start_workflow(
        "UserCreationWorkflow",
        user_data,
        id=workflow_id,
        task_queue=settings.USER_TASK_QUEUE,
    )
    return handle
