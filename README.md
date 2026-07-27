# SmartHealth — Intelligent Healthcare Operations Platform

A microservices-based healthcare platform built with Python/FastAPI. Handles user auth, patient records, provider scheduling, appointment booking, real-time analytics, and async notifications.

---

## Architecture

```
                    Client / API Gateway
    +----------+----------+----------+------------+
    |          |          |          |            |
+---+------++--+------++--+-------++--+-----------+
| auth-svc || patient- || provider-|| appt-svc    |
|  :8001   || svc:8002 || svc:8003 || :8004       |
+---+------++--+------++--+-------++--+-----------+
    |            |           |            |
    v            v           v            v
 auth-db     patient-db  provider-db  appt-db
(postgres)   (postgres)  (postgres)  (postgres)
    |                                    |
    | JWT blocklist     appointment.created / status_updated
    v                                    v
  Redis                            Apache Kafka
 (cache)                                 |
    ^                           +--------+-------+
    | analytics counters        | analytics-svc  |
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
                   |auth-svc   |     (postgres)    |
                   +--------+--+                   |
                            |                      |
                            +--Celery send_task----+
                            (on WF complete/failure)


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

### Billing Service — `localhost:8006`

All billing endpoints require a Bearer token. The `invoices/patient/{patient_id}` endpoint is also accessible by the patient themselves.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/invoices` | Admin, FD Staff | List all invoices |
| GET | `/invoices/{invoice_id}` | Admin, FD Staff | Get a single invoice by ID |
| GET | `/invoices/appointment/{appointment_id}` | Admin, FD Staff, Provider | Get the invoice for a specific appointment |
| GET | `/invoices/patient/{patient_id}` | Admin, FD Staff, Patient | List all invoices for a patient |

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
