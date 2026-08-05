from datetime import datetime, timedelta, timezone
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.reminder import send_day_before_reminder, send_hour_before_reminder
    from schemas import AppointmentReminderInput


@workflow.defn
class AppointmentReminderWorkflow:
    def __init__(self):
        self._cancelled = False

    @workflow.signal
    async def cancel(self):
        self._cancelled = True

    @workflow.run
    async def run(self, data: AppointmentReminderInput):
        date_parts = [int(x) for x in data.date.split("-")]
        time_parts = [int(x) for x in data.start_time.split(":")]
        appt_datetime = datetime(date_parts[0], date_parts[1], date_parts[2], time_parts[0], time_parts[1], tzinfo=timezone.utc)

        day_before = appt_datetime - timedelta(days=1) #reminder 1 day prior to appointmnet
        sleep_secs = (day_before - workflow.now()).total_seconds()
        if sleep_secs > 0:
            await workflow.sleep(timedelta(seconds=sleep_secs))

        if self._cancelled:
            return

        await workflow.execute_activity(
            send_day_before_reminder,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        hour_before = appt_datetime - timedelta(hours=1) #reminder 1 hour prior to appointmnet
        sleep_secs = (hour_before - workflow.now()).total_seconds()
        if sleep_secs > 0:
            await workflow.sleep(timedelta(seconds=sleep_secs))

        if self._cancelled:
            return

        await workflow.execute_activity(
            send_hour_before_reminder,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
