import os
from temporalio.client import Client

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
APPOINTMENT_TASK_QUEUE = os.getenv("APPOINTMENT_TASK_QUEUE", "appointment_validation_queue")


async def start_appointment_validation_workflow(appointment_data: dict, workflow_id: str):
    client = await Client.connect(TEMPORAL_HOST)
    handle = await client.start_workflow(
        "AppointmentValidationWorkflow",
        appointment_data,
        id=workflow_id,
        task_queue=APPOINTMENT_TASK_QUEUE,
    )
    return handle
