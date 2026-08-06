import requests

# fill these in before running
BASE_URL = "http://localhost:8007"
TOKEN = "PASTE_YOUR_ADMIN_TOKEN_HERE"

body = {
    "report_type": "daily_appointments",   # or department_utilization / patient_engagement / executive_snapshot
    "date": "2026-08-06",
}

resp = requests.post(
    f"{BASE_URL}/generate/report",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json=body,
    stream=True,
)

print(f"status: {resp.status_code}\n")

if resp.status_code != 200:
    print(resp.text)
else:
    full_text = ""
    for line in resp.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            full_text += line[len("data: "):]
    print(full_text)
