from temporalio.client import Client
from app.config import settings


async def start_appointment_validation_workflow(appointment_data: dict, workflow_id: str):
    client = await Client.connect(settings.TEMPORAL_HOST)
    handle = await client.start_workflow(
        "AppointmentValidationWorkflow",
        appointment_data,
        id=workflow_id,
        task_queue=settings.APPOINTMENT_TASK_QUEUE,
    )
    return handle
