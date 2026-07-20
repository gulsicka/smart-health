from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from app.config import settings
from app.schemas import WorkflowUserInput


async def start_user_creation_workflow(user_data: WorkflowUserInput, workflow_id: str):
    client = await Client.connect(
        settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE,
        interceptors=[TracingInterceptor()],
    )
    handle = await client.start_workflow(
        "UserCreationWorkflow",
        user_data,
        id=workflow_id,
        task_queue=settings.USER_TASK_QUEUE,
    )
    return handle


async def start_update_user_role_workflow(user_data: WorkflowUserInput, workflow_id: str):
    client = await Client.connect(
        settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE,
        interceptors=[TracingInterceptor()],
    )
    handle = await client.start_workflow(
        "UpdateUserWorkflow",
        user_data,
        id=workflow_id,
        task_queue=settings.UPDATE_USER_ROLE_TASK_QUEUE,
    )
    return handle
