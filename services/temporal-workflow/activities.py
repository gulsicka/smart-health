from temporalio import activity
import httpx, os

_token = None  # add this

async def get_service_token(): #for internal auth
    global _token
    if _token: # token already existss
        return _token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('AUTH_SERVICE_URL')}/login",
            data={
                "username": os.getenv("SYSTEM_EMAIL"),
                "password": os.getenv("SYSTEM_PASSWORD")
            }
        )
        response.raise_for_status()
        _token = response.json()["access_token"]
    return _token

async def make_request(method: str, url: str, **kwargs):
    """Make an authenticated request with automatic token refresh on 401."""
    global _token
    token = await get_service_token()
    
    async with httpx.AsyncClient() as client:
        response = await getattr(client, method)(
            url,
            headers={"Authorization": f"Bearer {token}"},
            **kwargs
        )
        
        if response.status_code == 401:
            _token = None
            token = await get_service_token()
            response = await getattr(client, method)(
                url,
                headers={"Authorization": f"Bearer {token}"},
                **kwargs
            )
        
        response.raise_for_status()
        return response


@activity.defn
async def create_patient_record(user_data: dict):
    await make_request(
        "post",
        f"{os.getenv('PATIENT_SERVICE_URL')}/patients",
        json={"user_id": user_data["id"], "date_of_birth": user_data["date_of_birth"]}
    )


@activity.defn
async def create_provider_record(user_data: dict):
    await make_request(
        "post",
        f"{os.getenv('PROVIDER_SERVICE_URL')}/providers",
        json={"user_id": user_data["id"], "department_id": user_data.get("department_id")}
    )


@activity.defn
async def validate_appointment_entities(data: dict):
    await make_request("get", f"{os.getenv('PATIENT_SERVICE_URL')}/patients/{data['patient_id']}")
    await make_request("get", f"{os.getenv('PROVIDER_SERVICE_URL')}/providers/{data['provider_id']}")
    await make_request("get", f"{os.getenv('PROVIDER_SERVICE_URL')}/departments/{data['department_id']}")
    await make_request("get", f"{os.getenv('PROVIDER_SERVICE_URL')}/clinics/{data['clinic_id']}")

@activity.defn
async def check_provider_availability(data: dict):
    response = await make_request(
        "get",
        f"{os.getenv('PROVIDER_SERVICE_URL')}/providers/{data['provider_id']}/availability"
    )
    availability_list = response.json()
    for avail in availability_list:
        if (avail["date"] == data["date"] and
            avail["start_time"] <= data["start_time"] and
            avail["end_time"] >= data["end_time"]):
            return True
    raise Exception("Provider is not available at the requested time.")

@activity.defn
async def check_for_appointment_conflict(appointment: dict):
    response = await make_request(
        "get",
        f"{os.getenv('APPOINTMENT_SERVICE_URL')}/appointments",
    )
    appointments = response.json()
    for appt in appointments:
        if (appt["provider_id"] == appointment["provider_id"] and
            appt["date"] == appointment["date"] and
            appt["status"] in ["requested", "confirmed", "checked_in", "in_progress"] and
            appt["start_time"] < appointment["end_time"] and
            appt["end_time"] > appointment["start_time"]):
            raise Exception("Provider already has an appointment in this time slot.")
    await make_request(
        "post",
        f"{os.getenv('APPOINTMENT_SERVICE_URL')}/appointments/internal",
        json=appointment
    )
    
@activity.defn
async def failed_workflow(data: dict):
    print(f"Workflow failed: {data.get('error')}")
