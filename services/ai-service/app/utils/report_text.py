#builds PURE stat text stored as chunks at sync time — no prompt framing/labels in here,
#that gets added by report.py when it assembles the message to send to the LLM


def totals_stats(date_str, daily, appointments, providers, departments, clinics, patients):
    return [
        f"Report date: {date_str}",
        f"Total patients: {len(patients)}",
        f"Total providers: {len(providers)}",
        f"Total departments: {len(departments)}",
        f"Total clinics: {len(clinics)}",
        f"Total appointments (all time): {len(appointments)}",
        f"Appointments on {date_str}: {len(daily)}",
        "",
    ]


def day_status_stats(daily):
    statuses = {}
    for a in daily:
        statuses[a["status"]] = statuses.get(a["status"], 0) + 1

    cancelled = statuses.get("cancelled", 0)
    rate = (cancelled / len(daily) * 100) if daily else 0

    return [
        "Status counts for the day: " + (", ".join(f"{k}={v}" for k, v in statuses.items()) or "none"),
        f"Cancellation rate for the day: {rate:.1f}%",
        "",
    ]


def provider_daily_breakdown(daily, departments, provider_map, dept_map, user_map):
    #precomputed so the LLM never has to tally/group the raw appointment list itself —
    #that's exactly where it kept inventing "unknown providers" that don't exist
    counts_by_provider = {}
    for a in daily:
        counts_by_provider[a["provider_id"]] = counts_by_provider.get(a["provider_id"], 0) + 1

    lines = [f"Distinct providers scheduled on this date: {len(counts_by_provider)}", ""]

    for dept in departments:
        dept_provider_ids = [
            pid for pid in counts_by_provider
            if provider_map.get(pid, {}).get("department_id") == dept["id"]
        ]
        if not dept_provider_ids:
            continue
        lines.append(f"{dept['name']} — {len(dept_provider_ids)} provider(s) scheduled:")
        for pid in dept_provider_ids:
            prov = provider_map.get(pid, {})
            name = user_map.get(prov.get("user_id"), {}).get("name", "Unknown")
            lines.append(f"  - {name} (Provider ID {pid}): {counts_by_provider[pid]} appointment(s)")
    lines.append("")
    return lines


def day_appointment_lines(daily, provider_map, dept_map, user_map):
    lines = []
    for i, a in enumerate(daily, start=1):
        prov      = provider_map.get(a["provider_id"], {})
        prov_name = user_map.get(prov.get("user_id"), {}).get("name", "Unknown")
        dept_name = dept_map.get(prov.get("department_id"), {}).get("name", "Unknown")
        lines.append(f"- Appointment {i} of {len(daily)} at {a['start_time']}: {prov_name} (ID {prov.get('id')}, {dept_name}), status {a['status']}")
    return lines


def busiest_department(daily, provider_map, dept_map):
    counts = {}
    for a in daily:
        dept_id = provider_map.get(a["provider_id"], {}).get("department_id")
        if dept_id:
            counts[dept_id] = counts.get(dept_id, 0) + 1
    if not counts:
        return "N/A", 0
    busiest_id = max(counts, key=counts.get)
    return dept_map.get(busiest_id, {}).get("name", "Unknown"), counts[busiest_id]


def build_daily_report(date_str, appointments, providers, departments, clinics, patients, provider_map, dept_map, user_map):
    #returns (stats_text, records_text) as two separate PURE strings — report.py decides
    #how to frame/label them when building the prompt, they aren't baked in here
    daily = [a for a in appointments if str(a["date"]).startswith(date_str)]

    stats_lines = (
        totals_stats(date_str, daily, appointments, providers, departments, clinics, patients)
        + day_status_stats(daily)
        + provider_daily_breakdown(daily, departments, provider_map, dept_map, user_map)
    )
    stats_text = "\n".join(stats_lines)

    records_text = "\n".join(day_appointment_lines(daily, provider_map, dept_map, user_map)) or "No appointments recorded for this date."

    return stats_text, records_text


def build_executive_snapshot(date_str, appointments, providers, departments, clinics, patients, provider_map, dept_map):
    daily = [a for a in appointments if str(a["date"]).startswith(date_str)]
    busiest_name, busiest_count = busiest_department(daily, provider_map, dept_map)

    lines = (
        totals_stats(date_str, daily, appointments, providers, departments, clinics, patients)
        + day_status_stats(daily)
        + [f"Busiest department today: {busiest_name} ({busiest_count} appointments)"]
    )
    return "\n".join(lines)


def build_department_utilization(appointments, departments, provider_map, user_map):
    lines = []
    for dept in departments:
        dept_appts = [a for a in appointments if provider_map.get(a["provider_id"], {}).get("department_id") == dept["id"]]
        provider_counts = {}
        for a in dept_appts:
            provider_counts[a["provider_id"]] = provider_counts.get(a["provider_id"], 0) + 1

        active = len(provider_counts)
        busiest_prov_id = max(provider_counts, key=provider_counts.get, default=None)
        if busiest_prov_id:
            prov = provider_map.get(busiest_prov_id, {})
            busiest_name = user_map.get(prov.get("user_id"), {}).get("name", "Unknown")
            busiest_line = f"{busiest_name} (ID {busiest_prov_id}, {provider_counts[busiest_prov_id]} appointments)"
        else:
            busiest_line = "N/A"

        lines.append(
            f"Department {dept['name']} (ID {dept['id']}): {len(dept_appts)} appointments (all time), "
            f"{active} active providers, busiest provider: {busiest_line}"
        )
    return "\n".join(lines)


def build_patient_engagement(appointments, patients, user_map):
    counts = {}
    for a in appointments:
        counts[a["patient_id"]] = counts.get(a["patient_id"], 0) + 1

    engaged = sum(1 for p in patients if counts.get(p["id"], 0) > 0)
    avg = (len(appointments) / len(patients)) if patients else 0

    ranked = sorted(patients, key=lambda p: counts.get(p["id"], 0), reverse=True)
    top5_lines = []
    for p in ranked[:5]:
        name = user_map.get(p.get("user_id"), {}).get("name", "Unknown")
        top5_lines.append(f"- {name} (Patient ID {p['id']}): {counts.get(p['id'], 0)} appointment(s)")

    zero_lines = []
    for p in patients:
        if counts.get(p["id"], 0) == 0:
            name = user_map.get(p.get("user_id"), {}).get("name", "Unknown")
            zero_lines.append(f"- {name} (Patient ID {p['id']})")

    lines = [
        f"Total patients: {len(patients)}",
        f"Patients with at least one appointment: {engaged}",
        f"Patients with none: {len(patients) - engaged}",
        f"Average appointments per patient: {avg:.1f}",
        "",
        "Top 5 most engaged patients:",
    ] + (top5_lines or ["- none"]) + [
        "",
        "Patients with zero appointments:",
    ] + (zero_lines or ["- none"])

    return "\n".join(lines)
