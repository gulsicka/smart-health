import json
import random
from datetime import datetime, timedelta

# ─── CONFIGURE THESE ────────────────────────────────────────────────────────
# Paste in the actual IDs from your DB after running the user collection
PATIENT_IDS  = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
PROVIDER_IDS = [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
CLINIC_ID    = 1
DATE         = "2026-08-06"
SLOT_MINS    = 15          # appointment duration in minutes
# ────────────────────────────────────────────────────────────────────────────


def build_slots(start="09:00", end="17:00", duration=SLOT_MINS):
    slots, cur = [], datetime.strptime(start, "%H:%M")
    end_dt = datetime.strptime(end, "%H:%M")
    while cur + timedelta(minutes=duration) <= end_dt:
        nxt = cur + timedelta(minutes=duration)
        slots.append((cur.strftime("%H:%M:%S"), nxt.strftime("%H:%M:%S")))
        cur = nxt
    return slots


def generate(seed=42):
    random.seed(seed)
    slots = build_slots()

    # track booked slots per provider and per patient to avoid conflicts
    provider_busy = {pid: set() for pid in PROVIDER_IDS}
    patient_busy  = {pid: set() for pid in PATIENT_IDS}

    appointments = []

    patients = PATIENT_IDS[:]
    random.shuffle(patients)

    for patient_id in patients:
        # each patient gets 2–4 appointments with different providers
        num = random.randint(2, 4)
        providers = random.sample(PROVIDER_IDS, min(num, len(PROVIDER_IDS)))

        for provider_id in providers:
            free = [
                s for s in slots
                if s not in provider_busy[provider_id]
                and s not in patient_busy[patient_id]
            ]
            if not free:
                continue
            slot = random.choice(free)
            provider_busy[provider_id].add(slot)
            patient_busy[patient_id].add(slot)
            appointments.append({
                "patient_id":  patient_id,
                "provider_id": provider_id,
                "clinic_id":   CLINIC_ID,
                "date":        DATE,
                "start_time":  slot[0],
                "end_time":    slot[1],
            })

    # sort by provider then start time for readability
    appointments.sort(key=lambda a: (a["provider_id"], a["start_time"]))
    return appointments


if __name__ == "__main__":
    appts = generate()

    out_path = "postman_appointments.json"
    with open(out_path, "w") as f:
        json.dump(appts, f, indent=2)

    print(f"Generated {len(appts)} appointments → {out_path}")

    # quick conflict check
    seen = {}
    conflicts = 0
    for a in appts:
        key_p = (a["provider_id"], a["start_time"])
        key_pt = (a["patient_id"], a["start_time"])
        if key_p in seen or key_pt in seen:
            print(f"  CONFLICT: {a}")
            conflicts += 1
        seen[key_p] = True
        seen[key_pt] = True
    print(f"Conflicts found: {conflicts}")
