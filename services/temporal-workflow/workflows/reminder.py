from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from activities.reminder import send_day_before_reminder, send_hour_before_reminder
    from schemas import AppointmentReminderInput

@workflow.defn
class SendDayBeforeReminderWorkflow:
    @workflow.run
    async def run(self, data: AppointmentReminderInput):
        await workflow.execute_activity(
            send_day_before_reminder,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )


@workflow.defn
class SendHourBeforeReminderWorkflow:
    @workflow.run
    async def run(self, data: AppointmentReminderInput):
        await workflow.execute_activity(
            send_hour_before_reminder,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
