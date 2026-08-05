import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from config import settings
from temporalio.contrib.opentelemetry import TracingInterceptor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

resource = Resource.create({"service.name": "temporal-workflow"})
otel_provider = TracerProvider(resource=resource)
otel_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(otel_provider)
HTTPXClientInstrumentor().instrument()

from workflows.user_creation import UserCreationWorkflow
from workflows.appointment import AppointmentValidationWorkflow
from workflows.update_user_role import UpdateUserWorkflow
from workflows.reminder import AppointmentReminderWorkflow

from activities.user import (
    create_patient_record,
    create_provider_record,
    activate_user,
    fail_user,
    delete_patient_record,
    delete_provider_record,
    remove_user_role_on_failure,
    notify_user_created_activity,
    notify_user_creation_failed_activity,
    notify_user_role_updated_activity,
    notify_user_role_update_failed_activity,
)
from activities.appointment import (
    validate_appointment_entities,
    check_provider_availability,
    check_for_appointment_conflict,
    notify_booking_failed,
)
from activities.common import failed_workflow
from activities.reminder import send_day_before_reminder, send_hour_before_reminder

TEMPORAL_HOST = settings.TEMPORAL_HOST
USER_TASK_QUEUE = settings.USER_TASK_QUEUE
APPOINTMENT_TASK_QUEUE = settings.APPOINTMENT_TASK_QUEUE
UPDATE_USER_ROLE_TASK_QUEUE = settings.UPDATE_USER_ROLE_TASK_QUEUE


async def main():
    while True:
        try:
            client = await Client.connect(TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE, interceptors=[TracingInterceptor()])
            break
        except Exception:
            print("Waiting for Temporal...")
            await asyncio.sleep(3)

    user_creation_worker = Worker(
        client,
        task_queue=USER_TASK_QUEUE,
        workflows=[UserCreationWorkflow],
        activities=[
            create_patient_record,
            create_provider_record,
            activate_user,
            fail_user,
            delete_patient_record,
            delete_provider_record,
            notify_user_created_activity,
            notify_user_creation_failed_activity,
        ],
        interceptors=[TracingInterceptor()],
    )

    appointment_validation_worker = Worker(
        client,
        task_queue=APPOINTMENT_TASK_QUEUE,
        workflows=[AppointmentValidationWorkflow],
        activities=[validate_appointment_entities, check_provider_availability, check_for_appointment_conflict, failed_workflow, notify_booking_failed],
        interceptors=[TracingInterceptor()],
    )
    
    update_user_role_worker = Worker(
        client,
        task_queue=UPDATE_USER_ROLE_TASK_QUEUE,
        workflows=[UpdateUserWorkflow],
        activities=[
            create_patient_record,
            create_provider_record,
            remove_user_role_on_failure,
            notify_user_role_updated_activity,
            notify_user_role_update_failed_activity,
        ],
        interceptors=[TracingInterceptor()],
    )

    reminder_worker = Worker(
        client,
        task_queue=settings.REMINDER_TASK_QUEUE,
        workflows=[AppointmentReminderWorkflow],
        activities=[send_day_before_reminder, send_hour_before_reminder],
        interceptors=[TracingInterceptor()],
    )

    await asyncio.gather(
        user_creation_worker.run(),
        appointment_validation_worker.run(),
        update_user_role_worker.run(),
        reminder_worker.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())
