# SmartHealth — Intelligent Healthcare Operations Platform

A microservices-based healthcare platform built with Python/FastAPI. Handles user auth, patient records, provider scheduling, appointment booking, real-time analytics, and async notifications.

---

## Architecture

```
                    Client / API Gateway
    +----------+----------+----------+-----------+-----------+
    |          |          |          |           |           |
+---+------++--+------++--+-------++--+---------++-+---------+
| auth-svc || patient- || provider-|| appt-svc  || ai-svc    |
|  :8001   || svc:8002 || svc:8003 || :8004     || :8007     |
+---+------++--+------++--+-------++--+---------++-+---------+
    |            |           |            |            |
    v            v           v            v            v
 auth-db     patient-db  provider-db  appt-db       ai-db
(postgres)   (postgres)  (postgres)  (postgres)   (pgvector
    |                                    |          :5441)
    | JWT blocklist     appointment.created /         |
    v                     status_updated              |
  Redis                            Apache Kafka <-----+
 (cache)                                 |    ai.events (ai.chat /
    ^                           +--------+-------+   ai.report /
    | analytics counters        | analytics-svc  |   ai.communication)
    +---------------------------|    :8005       |
                                +--------+-------+
                                         |         \
                                         |      analytics-db
                                  Celery | (TimescaleDB :5435)
                                  send_task
                                         |
    auth-svc ---+                        v
    appt-svc ---+---> Temporal :7233  RabbitMQ <--+
                      temporal-ui:8080    |        |
                            |    +--------+------+ |
                   +--------+--+ |notification-  | |
                   |temporal-  | |svc (Celery    | |
                   |workflow   | |worker)        | |
                   |(worker)   | +--------+------+ |
                   |calls:     |          |        |
                   |patient-,  |          v        |
                   |provider-, |   notification-db |
                   |auth-svc,  |     (postgres)    |
                   |ai-svc     |                   |
                   +--------+--+                   |
                            |                      |
                            +--Celery send_task----+
                            (on WF complete/failure)


  billing-svc :8006 ---> billing-db (postgres :5440)
        ^
        +--- consumes appointments.events from Kafka (see Billing below)


  GenAI Layer — ai-service :8007
  +-----------------------------------------------------------------------+
  |                                                                       |
  |  Agentic tool-calling (/chat, /generate/communication,                |
  |  /generate/report — one shared ReAct loop, app/agent.py):             |
  |    ai-svc --LLM decides which tool(s) to call, live, per request-->   |
  |      get_patient/provider/clinic/department/user --> patient-,       |
  |                                             provider-, auth-svc       |
  |      get_appointment(s)_by_* ------------------------> appt-svc       |
  |      get_daily_appointment_stats, get_department_utilization_stats,  |
  |        get_patient_engagement_stats, get_executive_snapshot_stats     |
  |        (fetch live data, compute deterministically in Python)         |
  |      search_documents ---------------> ai-db (pgvector, PDFs only)    |
  |    no bulk/raw entity dump is ever exposed to the LLM as a tool       |
  |                                                                       |
  |  Document ingestion (PDF only — the only thing pgvector stores):      |
  |    ai-svc --POST /ingest/pdf--> starts PdfIngestionWorkflow           |
  |      (temporal-workflow) --one activity per page--> ai-svc            |
  |      (hash-diff unchanged pages, replace changed pages,               |
  |       clean up orphan pages) --embed (all-MiniLM-L6-v2)--> ai-db      |
  |                                                                       |
  |  Kafka publish (AI usage analytics):                                  |
  |    ai-svc --[ai.events: ai.chat / ai.report / ai.communication]-->    |
  |                              analytics-svc  (GET /analytics/ai)       |
  |                                                                       |
  |  Temporal Schedules (reminder triggering):                            |
  |    appt-svc --[appointments.events]--> ai-svc kafka_consumer          |
  |      --create_schedule (day-before / hour-before, one-shot)-->        |
  |      Temporal --fires at scheduled time--> SendDayBeforeReminder /    |
  |      SendHourBeforeReminderWorkflow --POST /generate/reminder-->      |
  |      ai-svc --> Groq LLM                                              |
  |      (both schedules cancelled if the appointment is cancelled)       |
  |                                                                       |
  |  External LLM:                                                        |
  |    ai-svc --LangChain (ChatGroq)--> Groq API (model set via           |
  |                                      GROQ_MODEL env var)              |
  |                                                                       |
  +-----------------------------------------------------------------------+


  Orphan Data / Cascade Cleanup (Kafka event chain)
  +-----------------------------------------------------------------------+
  |                                                                       |
  |  DELETE /users/{id}                                                   |
  |    auth-svc --[users.events: user.deleted]--> patient-svc            |
  |                                               provider-svc            |
  |    patient-svc  --[patients.events: patient.deleted]--> auth-svc     |
  |                                                          (remove role)|
  |                                               appt-svc (cancel appts)|
  |    provider-svc --[providers.events: provider.deleted]--> auth-svc   |
  |                                                           (remove role|
  |                                               appt-svc (cancel appts)|
  |                                                                       |
  |  DELETE /patients/{id} --> patients.events --> auth removes role      |
  |                                            --> appt cancels appts     |
  |  DELETE /providers/{id} --> providers.events --> auth removes role    |
  |                                             --> appt cancels appts    |
  +-----------------------------------------------------------------------+


  Billing (Kafka-driven, fully event-sourced)
  +-----------------------------------------------------------------------+
  |                                                                       |
  |  appointments.events --> billing-svc :8006 --> billing-db             |
  |                                               (Postgres :5440)        |
  |                                                                       |
  |    appointment.created        --> Invoice created (status: pending)   |
  |    appointment.status_updated:                                        |
  |      completed                --> Invoice status: paid                |
  |      cancelled / no_show      --> Invoice status: refunded            |
  |                                                                       |
  |  billing-svc --> Redis (SET NX billing:event:{id}) for idempotency   |
  |  billing-svc exposes read-only invoice endpoints (see API Overview)   |
  |                                                                       |
  +-----------------------------------------------------------------------+


  Observability
  +------------------------------------------------------------------+
  |                                                                  |
  |  all services --OTLP push (port 4317)--> Jaeger :16686          |
  |                                          (trace viewer)         |
  |                                                                  |
  |  Prometheus :9090 --scrape /metrics--> all services             |
  |        |                                                         |
  |        +-> Grafana :3000 (dashboards)                           |
  |                                                                  |
  +------------------------------------------------------------------+
```

---

## Services

| Service | Port | Responsibility |
|---|---|---|
| auth-service | 8001 | JWT auth, users, roles, logout with Redis blocklist |
| patient-service | 8002 | Patient profile CRUD |
| provider-service | 8003 | Providers, clinics, departments, availability |
| appointment-service | 8004 | Booking, status updates, Kafka event publishing |
| analytics-service | 8005 | Kafka consumer, Redis counters, TimescaleDB event store, analytics API |
| billing-service | 8006 | Kafka consumer, fixed-fee invoice lifecycle (pending → paid / refunded), per-appointment billing |
| ai-service | 8007 | GenAI layer — agentic tool-calling chat, live report generation, AI-drafted communications, Temporal-driven PDF ingestion, pgvector document store |
| notification-service | — | Celery worker, persists notifications to Postgres |
| temporal-workflow | — | Temporal worker for user creation + appointment validation workflows |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI (Python) |
| Databases | PostgreSQL (per-service) |
| Auth | JWT + Redis blocklist (jti-based logout) |
| Workflow Orchestration | Temporal |
| Message Streaming | Apache Kafka (KRaft, no Zookeeper) |
| Async Task Queue | Celery + RabbitMQ |
| Caching / Counters | Redis |
| Time-Series Analytics DB | TimescaleDB (PostgreSQL extension) |
| Vector Store | pgvector (PostgreSQL extension) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Groq API (model configurable via `GROQ_MODEL`, currently `openai/gpt-oss-20b`) via LangChain, tool-calling agent |
| Monitoring | Prometheus + Grafana |
| Containerization | Docker + Docker Compose |

---

## Setup

### Prerequisites

- Docker + Docker Compose
- `.env` file in project root (see below)

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
CLUSTER_ID=your-base64-kafka-cluster-uuid
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-20b
```

Generate a Kafka `CLUSTER_ID`:
```bash
python -c "import uuid, base64; print(base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b'=').decode())"
```

### Run

```bash
docker compose up --build
```

All services start automatically with health checks and dependency ordering.

### Stopping

```bash
docker compose down          # stop containers
docker compose down -v       # stop + delete all volumes (fresh state)
```

---

## API Overview

### Auth Service — `localhost:8001`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/login` | None | Login, returns JWT |
| POST | `/logout` | Bearer | Invalidates token via Redis |
| POST | `/users` | Admin/FD Staff | Create user |
| GET | `/users` | Admin | List all users |
| GET | `/users/{id}` | Admin | Get user by ID |
| PUT | `/users/{id}` | Admin | Update user |
| PATCH | `/users/{id}/activate` | Admin | Activate user |
| DELETE | `/users/{id}` | Admin | Soft-delete user, triggers Kafka cascade cleanup |
| POST | `/roles` | Admin | Create role |
| GET | `/roles` | Admin | List roles |
| DELETE | `/roles/{id}` | Admin | Delete role |

### Patient Service — `localhost:8002`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/patients` | Create patient profile |
| GET | `/patients` | List all patients |
| GET | `/patients/{id}` | Get patient |
| PUT | `/patients/{id}` | Update patient |
| DELETE | `/patients/{id}` | Soft-delete patient, removes patient role from user, cancels appointments |

### Provider Service — `localhost:8003`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/providers` | Create provider |
| GET | `/providers` | List providers |
| GET | `/providers/{id}` | Get provider |
| POST | `/providers/{id}/availability` | Add availability slot |
| POST | `/providers/{id}/setup-availability` | Bulk availability setup |
| GET | `/providers/{id}/availability` | Get availability |
| POST | `/departments` | Create department |
| GET | `/departments` | List departments |
| POST | `/clinics` | Create clinic |
| GET | `/clinics` | List clinics |
| POST | `/clinics/{id}/departments` | Add department to clinic |

### Appointment Service — `localhost:8004`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/appointments` | Book appointment (triggers Temporal workflow) |
| GET | `/appointments` | List appointments |
| GET | `/appointments/{id}` | Get appointment |
| PATCH | `/appointments/{id}/status` | Update status (created → confirmed → completed/cancelled) |
| GET | `/providers/{id}/booked-slots` | Get booked time slots for a provider |
| DELETE | `/appointments/{id}` | Delete appointment |

### Analytics Service — `localhost:8005`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics` | Total appointments, completions, cancellations, daily breakdowns (Redis counters) |
| GET | `/analytics/filter` | Filter events by date range, clinic, provider — grouped by day and event type (TimescaleDB) |
| GET | `/analytics/total-created` | Count of a specific event type between two dates (TimescaleDB) |
| GET | `/analytics/ai` | AI assistant usage, questions asked/answered, generated communication usage by type (admin) |

### Billing Service — `localhost:8006`

All billing endpoints require a Bearer token. The `invoices/patient/{patient_id}` endpoint is also accessible by the patient themselves.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/invoices` | Admin, FD Staff | List all invoices |
| GET | `/invoices/{invoice_id}` | Admin, FD Staff | Get a single invoice by ID |
| GET | `/invoices/appointment/{appointment_id}` | Admin, FD Staff, Provider | Get the invoice for a specific appointment |
| GET | `/invoices/patient/{patient_id}` | Admin, FD Staff, Patient | List all invoices for a patient |

### AI Service — `localhost:8007`

All AI endpoints are admin-only.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Natural-language Q&A over platform data — agentic tool-calling loop, streamed live as SSE |
| POST | `/generate/report` | Generate a report (`daily_appointments`, `department_utilization`, `patient_engagement`, `executive_snapshot`) — agent calls a dedicated stats tool that computes live numbers, then narrates |
| POST | `/generate/communication` | Draft a `follow_up`, `service_recommendation`, `preventive_care`, or `operational_assistance` message — agent looks up the live patient/provider/clinic record via tools |
| POST | `/generate/reminder` | Draft an appointment reminder (`day_before` / `hour_before`) — called by the Temporal-Schedule-triggered reminder workflow |
| POST | `/ingest` | Ingest arbitrary raw text under a given source key |
| POST | `/ingest/pdf` | Ingest a PDF via a Temporal workflow (`PdfIngestionWorkflow`) — one activity per page, hash-diffed so unchanged pages are skipped |
| POST | `/retrieve` | Debug endpoint — return the raw retrieved PDF chunks and scores for a query |

---

## Key Design Decisions

**JWT Logout with Redis blocklist** — Each token carries a `jti` (UUID). On logout, the `jti` is stored in Redis with TTL equal to the remaining token lifetime. Every authenticated request checks the blocklist before proceeding.

**Kafka for event streaming** — appointment-service publishes `appointment.created` and `appointment.status_updated` events to Kafka. analytics-service consumes them with deduplication (Redis `SET NX`) to ensure idempotent processing.

**Temporal for workflow orchestration** — User creation and appointment booking run as Temporal workflows, giving retries, visibility, and compensation logic out of the box.

**Celery + RabbitMQ for notifications** — analytics-service dispatches notification tasks by name (`send_task("tasks.send_booking_confirmation", ...)`), keeping services decoupled. notification-service runs as a Celery worker with no HTTP server.

**Orphan data handling via Kafka event chain** — Since there are no cross-DB foreign keys, deleting a record in one service does not automatically cascade. Three flows are handled: (1) deleting a patient record removes the patient role from the user and cancels their appointments; (2) deleting a provider record removes the provider role from the user and cancels their appointments; (3) deleting a user soft-deletes their patient and provider records and cancels all active appointments. Soft delete (`is_deleted` flag on patients/providers, `status=deleted` on users) is used instead of hard delete so medical records are preserved for audit and legal compliance.

**TimescaleDB for analytics** — Every appointment event consumed from Kafka is persisted to a TimescaleDB hypertable (`appointment_events`). TimescaleDB is a PostgreSQL extension that partitions data automatically by time, making range queries and aggregations fast. `time_bucket()` is used to group events into daily buckets for filtered analytics. Redis counters handle real-time totals; TimescaleDB handles historical, filterable queries.

**Per-service databases** — Each service owns its Postgres database. No cross-service foreign keys; references are by ID only.

**CRUD package pattern** — Each service uses a `crud/` package with one file per model, re-exported via `__init__.py`. Router imports don't change when logic is split.

**LLM for language, code for math** — No GenAI endpoint ever asks the LLM to compute a number. Every total, count, and percentage is calculated deterministically in Python (`utils/report_text.py`), exposed to the agent as a set of report-stats tools (`get_daily_appointment_stats`, `get_department_utilization_stats`, `get_patient_engagement_stats`, `get_executive_snapshot_stats`) that fetch live data from the owning services and compute the numbers at request time — nothing is precomputed or cached. This came out of real failures — given a raw appointment list the model miscounted totals (mistaking a database ID for a count) and invented providers that didn't exist. The system prompt requires the agent to call the relevant stats tool first and use its numbers exactly as returned; the LLM only narrates.

**Agentic tool-calling instead of query parsing** — `/chat`, `/generate/communication`, and `/generate/report` share one ReAct tool-calling loop (`app/agent.py`). Rather than regex-parsing entity IDs out of a query or pre-fetching context by hand (both brittle and inconsistent across endpoints), a scoped tool library (`app/tools.py`) is bound to the LLM and it decides which tool(s) to call — single-entity lookups only (`get_patient`, `get_provider`, `get_appointment`, etc.), never a bulk/raw dump. Every round of the loop is streamed live over SSE (including visible `[calling get_patient...]` status events), not just the final answer, so the tool-calling is genuinely observable, not simulated. Any ID a tool surfaces (`department_id`, `user_id`, `clinic_id`) must be resolved via the matching tool before being shown to the user — enforced explicitly in the system prompt.

**pgvector scoped to documents only** — Early on, pgvector stored chunks for every entity (patients, providers, appointments) plus precomputed report stats, kept in sync via a `/ingest/sync` rebuild and incremental Kafka consumers. That meant every answer could be reading data that was stale as of the last sync. pgvector now stores only ingested PDF/document content; all entity and report data is fetched live via the tool-calling agent instead, so there's no staleness window and no sync step to remember to run.

**Temporal workflow for PDF ingestion** — Parsing and embedding a PDF used to run inline inside the `/ingest/pdf` request with no retry and no isolation — one bad page failed the whole upload. It's now a Temporal workflow (`PdfIngestionWorkflow`) with one activity per page: each page is hashed and diffed against what's stored (unchanged pages are skipped, changed pages are replaced in a single transaction), a failed page is retried per Temporal's activity retry policy without failing the rest of the upload, and pages dropped from a shorter re-upload are cleaned up (orphan-page deletion).

**Temporal Schedules instead of sleeping workflows for reminders** — Appointment reminders originally ran as a long-lived workflow that called `workflow.sleep()` until the reminder time, which isn't the idiomatic Temporal pattern for "run this once in the future." Reminders are now Temporal Schedules: on `appointment.created`, `ai-service`'s Kafka consumer creates two one-shot schedules (`SendDayBeforeReminderWorkflow`, `SendHourBeforeReminderWorkflow`) via `ScheduleActionStartWorkflow` + `ScheduleCalendarSpec`, each with `remaining_actions=1`. Both schedules are deleted if the appointment is later cancelled.

**Event-driven billing** — billing-service has no HTTP calls from appointment-service; it is a pure Kafka consumer on `appointments.events` (the same topic analytics-service uses). On `appointment.created` it creates a pending invoice for a fixed $100 consultation fee. On `appointment.status_updated`, it marks the invoice paid (completed) or refunded (cancelled / no_show). Kafka event deduplication uses Redis `SET NX` on `billing:event:{event_id}` with a 24h TTL, with a DB-level unique constraint on `appointment_id` as a second safety net. The service exposes read-only REST endpoints for querying invoices by ID, appointment, or patient.

---

## Monitoring

- **Prometheus** — `localhost:9090` — scrapes `/metrics` from all FastAPI services every 15s
- **Grafana** — `localhost:3000` — dashboards for request rate, latency (p99), error rate per service (admin/admin)
- **Kafdrop** — `localhost:9000` — Kafka topic and message browser
- **RabbitMQ Management** — `localhost:15672` — queue and consumer visibility (guest/guest)
- **Temporal UI** — `localhost:8080` — workflow execution history

---

## Swagger Docs

Each service exposes interactive API docs at `/docs`:

- Auth: `http://localhost:8001/docs`
- Patient: `http://localhost:8002/docs`
- Provider: `http://localhost:8003/docs`
- Appointment: `http://localhost:8004/docs`
- Analytics: `http://localhost:8005/docs`
- Billing: `http://localhost:8006/docs`
- AI: `http://localhost:8007/docs`

---

## Database Schema

Each service owns its own isolated Postgres database. Cross-service references use plain integer IDs — no cross-database foreign keys.

### billing-db — `invoices`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | integer | PK, auto-increment | Invoice primary key |
| `appointment_id` | integer | NOT NULL, UNIQUE, indexed | References the appointment in appointment-db (no FK) |
| `patient_id` | integer | NOT NULL, indexed | References the user/patient in auth-db / patient-db (no FK) |
| `provider_id` | integer | NOT NULL | References the provider in provider-db (no FK) |
| `clinic_id` | integer | NOT NULL | References the clinic in provider-db (no FK) |
| `amount` | numeric(10,2) | NOT NULL | Fixed consultation fee (default $100.00) |
| `status` | varchar | NOT NULL, default `pending` | Invoice status: `pending` \| `paid` \| `refunded` |
| `appointment_date` | varchar | nullable | Date of the appointment (denormalised from the Kafka event) |
| `created_at` | timestamp | NOT NULL, default now() | Record creation time |
| `updated_at` | timestamp | NOT NULL, default now() | Last update time (auto-updated on write) |

**Status transitions driven by Kafka `appointments.events`:**

```
appointment.created              → status: pending
appointment.status_updated:
  status = completed             → status: paid
  status = cancelled / no_show  → status: refunded
```

**Relations to other services (by ID, no FK):**
- `appointment_id` → `appointments.id` in appointment-db (unique — one invoice per appointment)
- `patient_id` → `users.id` / `patients.user_id` in auth-db / patient-db
- `provider_id` → `providers.user_id` in provider-db
- `clinic_id` → `clinics.id` in provider-db

### ai-db — `document_chunks`

pgvector now stores only ingested PDF/document content — no entity or report data. Entity records are fetched live via tool calls, and report statistics are computed live per request (see Key Design Decisions above).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | integer | PK, auto-increment | Chunk primary key |
| `source` | varchar | NOT NULL, indexed | The ingested document's source label (e.g. a handbook name) |
| `content` | text | NOT NULL | The chunk text (markdown, via PyMuPDF4LLM) |
| `embedding` | vector(384) | NOT NULL | `all-MiniLM-L6-v2` embedding of `content` |
| `page_hash` | varchar | nullable | Hash of this page's extracted text, used to skip re-embedding unchanged pages on re-upload |
| `page_number` | integer | nullable | Which page of the source PDF this chunk came from |
| `created_at` | timestamp | default now() | Record creation time |

Ingestion hashes and diffs per page rather than per file: unchanged pages are skipped, changed pages have their chunks replaced in one transaction (`replace_page_chunks`), and pages present in the DB but absent from a shorter re-upload are deleted (orphan-page cleanup). Retrieval (`search_documents` tool, used by `/chat`, `/generate/communication`, `/generate/report`, and the `/retrieve` debug endpoint) is plain pgvector cosine-similarity search over these chunks.

### analytics-db — `ai_interaction_events`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | integer | PK (composite with `time`), auto-increment | Event row key |
| `time` | timestamp | PK (composite with `id`), NOT NULL | When the interaction happened |
| `event_type` | varchar | NOT NULL | `ai.chat` \| `ai.communication` \| `ai.report` |
| `status` | varchar | NOT NULL | `answered` \| `failed` |
| `communication_type` | varchar | nullable | Set only for `ai.communication` events |
| `user_id` | integer | nullable | The admin who triggered the interaction |

Populated by analytics-service consuming the `ai.events` Kafka topic; Redis counters serve the real-time totals behind `GET /analytics/ai`.
