# SmartHealth — Intelligent Healthcare Operations Platform

A microservices-based healthcare platform built with Python/FastAPI. Handles user auth, patient records, provider scheduling, appointment booking, real-time analytics, and async notifications.

---

## Architecture

```
                          Client / API Gateway
           ┌──────────────┬──────────────┬──────────────┐
           │              │              │              │
    ┌──────┴──────┐ ┌─────┴──────┐ ┌────┴──────┐ ┌────┴───────────┐
    │auth-service │ │patient-    │ │provider-  │ │appointment-    │
    │   :8001     │ │service     │ │service    │ │service         │
    │             │ │:8002       │ │:8003      │ │:8004           │
    └──────┬──────┘ └─────┬──────┘ └────┬──────┘ └────┬───────────┘
           │              │             │              │
           ▼              ▼             ▼              ▼
        auth-db       patient-db    provider-db    appoint-db
      (postgres)      (postgres)    (postgres)     (postgres)
           │                                         │
           │ JWT blocklist                           │ appointment.created
           ▼                                         │ appointment.status_updated
         Redis  ◄─────────────────────┐              ▼
       (cache)    analytics counters  │         Apache Kafka
                                      │              │
                               ┌──────┴──────┐       │
                               │ analytics-  │◄──────┘
                               │ service     │
                               │ :8005       │
                               └──────┬──────┘
                                      │ Celery tasks (send_task)
                                      ▼
                                  RabbitMQ
                                      │
                               ┌──────┴──────────────┐
                               │ notification-service │
                               │ (Celery worker)      │
                               └──────┬───────────────┘
                                      │
                                      ▼
                                notification-db
                                  (postgres)


  Temporal :7233  ◄──── auth-service (user creation workflow)
  (Workflow           ◄──── appointment-service (booking validation workflow)
  Orchestration)
  temporal-ui :8080


  Observability
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  all services ──OTLP traces──► Jaeger :16686 (trace viewer)    │
  │                                                                 │
  │  Prometheus :9090 ──scrape /metrics──► all services            │
  │       │                                                         │
  │       └──► Grafana :3000 (dashboards)                          │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Services

| Service | Port | Responsibility |
|---|---|---|
| auth-service | 8001 | JWT auth, users, roles, logout with Redis blocklist |
| patient-service | 8002 | Patient profile CRUD |
| provider-service | 8003 | Providers, clinics, departments, availability |
| appointment-service | 8004 | Booking, status updates, Kafka event publishing |
| analytics-service | 8005 | Kafka consumer, Redis counters, analytics API |
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
| DELETE | `/users/{id}` | Admin | Delete user |
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
| DELETE | `/patients/{id}` | Delete patient |

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
| GET | `/analytics` | Total appointments, completions, cancellations, daily breakdowns |

---

## Key Design Decisions

**JWT Logout with Redis blocklist** — Each token carries a `jti` (UUID). On logout, the `jti` is stored in Redis with TTL equal to the remaining token lifetime. Every authenticated request checks the blocklist before proceeding.

**Kafka for event streaming** — appointment-service publishes `appointment.created` and `appointment.status_updated` events to Kafka. analytics-service consumes them with deduplication (Redis `SET NX`) to ensure idempotent processing.

**Temporal for workflow orchestration** — User creation and appointment booking run as Temporal workflows, giving retries, visibility, and compensation logic out of the box.

**Celery + RabbitMQ for notifications** — analytics-service dispatches notification tasks by name (`send_task("tasks.send_booking_confirmation", ...)`), keeping services decoupled. notification-service runs as a Celery worker with no HTTP server.

**Per-service databases** — Each service owns its Postgres database. No cross-service foreign keys; references are by ID only.

**CRUD package pattern** — Each service uses a `crud/` package with one file per model, re-exported via `__init__.py`. Router imports don't change when logic is split.

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
