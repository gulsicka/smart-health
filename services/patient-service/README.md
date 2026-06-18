# patient-service

Manages patient records and audit logs. All endpoints require a valid JWT issued by auth-service.

## Stack
- Python 3.12 · FastAPI · SQLAlchemy · Alembic · PostgreSQL
- python-jose (JWT verification) · Pydantic v2

## Running

```bash
docker-compose up --build
```

Service runs on `http://localhost:8002` — Swagger at `http://localhost:8002/docs`

## Database

- Container: `patient-db` (internal) · exposed on `localhost:5434`
- Database: `patient_db`
- Migrations: Alembic (`alembic upgrade head` from `services/patient-service/`)

## API

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| POST | `/patients` | Create patient | Yes |
| GET | `/patients` | List all patients | Yes |
| GET | `/patients/{id}` | Get patient by ID | Yes |
| PUT | `/patients/{id}` | Update patient | Yes |
| DELETE | `/patients/{id}` | Delete patient | Yes |

## Auth

All routes (except `/health`) require:
```
Authorization: Bearer <token>
```

`user_id` is extracted from the JWT — never passed in the request body. JWT is verified locally via shared secret (stateless — no call to auth-service).

## Schema

```
patients    — id, name, email, number, date_of_birth, user_id (plain int — no FK, references auth_db.users)
audit_logs  — id, entity_id, action, timestamp, changed_by
```

> `user_id` has no FK constraint — patient-service and auth-service have isolated databases. Consistency is enforced via JWT.
> `audit_log.entity_id` is a plain int — preserves history even after a patient is deleted.
