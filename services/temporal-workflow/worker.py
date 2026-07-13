import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from config import settings

from workflows.user_creation import UserCreationWorkflow
from workflows.appointment import AppointmentValidationWorkflow
from workflows.provider_availability import ProviderAvailabilityWorkflow

from activities.user_creation import (
    create_patient_record,
    create_provider_record,
    activate_user,
    fail_user,
    delete_patient_record,
)
from activities.appointment import (
    validate_appointment_entities,
    check_provider_availability,
    check_for_appointment_conflict,
)
from activities.provider import setup_provider_availability
from activities.common import failed_workflow

TEMPORAL_HOST = settings.TEMPORAL_HOST
USER_TASK_QUEUE = settings.USER_TASK_QUEUE
APPOINTMENT_TASK_QUEUE = settings.APPOINTMENT_TASK_QUEUE
PROVIDER_TASK_QUEUE = settings.PROVIDER_TASK_QUEUE

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
        activities=[create_patient_record, create_provider_record, activate_user, fail_user, delete_patient_record],
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