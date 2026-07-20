from datetime import date, timedelta
from temporalio import activity
import clients.provider.api as provider_client
from schemas import ProviderScheduleInput


@activity.defn
async def setup_provider_availability(data: ProviderScheduleInput):
    today = date.today()
    for i in range(30):
        d = today + timedelta(days=i)
        if d.strftime("%A") in data.working_days:
            await provider_client.create_availability(
                provider_id=data.provider_id,
                clinic_id=data.clinic_id,
                date=d.isoformat(),
                start_time=data.start_time,
                end_time=data.end_time,
            )
