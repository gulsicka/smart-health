from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from app.config import settings
from app.schemas import WorkflowAppointmentInput


async def start_appointment_validation_workflow(appointment_data: WorkflowAppointmentInput, workflow_id: str):
    client = await Client.connect(
        settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE,
        interceptors=[TracingInterceptor()],
    )
    handle = await client.start_workflow(
        "AppointmentValidationWorkflow",
        appointment_data,
        id=workflow_id,
        task_queue=settings.APPOINTMENT_TASK_QUEUE,
    )
    return handle
