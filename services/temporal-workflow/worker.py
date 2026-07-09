import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import AppointmentValidationWorkflow, UserCreationWorkflow, ProviderAvailabilityWorkflow
from activities import check_for_appointment_conflict, check_provider_availability, create_patient_record, create_provider_record, validate_appointment_entities, setup_provider_availability, failed_workflow

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
USER_TASK_QUEUE = os.getenv("USER_TASK_QUEUE")
APPOINTMENT_TASK_QUEUE = os.getenv("APPOINTMENT_TASK_QUEUE")
PROVIDER_TASK_QUEUE = os.getenv("PROVIDER_TASK_QUEUE")

async def main():

    while True:
        # the worker was starting before temporal was ready, so we retry connection and wait for temporal to get ready
        try:
            client = await Client.connect(TEMPORAL_HOST)
            break
        except Exception:
            print("Waiting for Temporal...")
            await asyncio.sleep(3)

    user_creation_worker = Worker(
        client,
        task_queue=USER_TASK_QUEUE,
        workflows=[UserCreationWorkflow],
        activities=[create_patient_record, create_provider_record, failed_workflow],
    )

    appointment_validation_worker = Worker(
        client,
        task_queue=APPOINTMENT_TASK_QUEUE,
        workflows=[AppointmentValidationWorkflow],
        activities=[validate_appointment_entities, check_provider_availability, check_for_appointment_conflict, failed_workflow],
    )

    provider_availability_worker = Worker(
        client,
        task_queue=PROVIDER_TASK_QUEUE,
        workflows=[ProviderAvailabilityWorkflow],
        activities=[setup_provider_availability, failed_workflow],
    )

    await asyncio.gather(
        user_creation_worker.run(),
        appointment_validation_worker.run(),
        provider_availability_worker.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())