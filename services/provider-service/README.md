# provider-service

Manages providers, departments, specialties, clinics, and availability slots. All endpoints require a valid JWT issued by auth-service.

## Stack
- Python 3.12 · FastAPI · SQLAlchemy · Alembic · PostgreSQL
- python-jose (JWT verification) · Pydantic v2

## Running

```bash
docker-compose up --build
```

Service runs on `http://localhost:8003` — Swagger at `http://localhost:8003/docs`

## Database

- Container: `provider-db` (internal) · exposed on `localhost:5435`
- Database: `provider_db`
- Migrations: Alembic (`alembic upgrade head` from `services/provider-service/`)

## API

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| POST | `/departments` | Create department | Yes |
| GET | `/departments` | List departments | Yes |
| POST | `/specialties` | Create specialty | Yes |
| GET | `/specialties` | List specialties | Yes |
| POST | `/clinics` | Create clinic | Yes |
| GET | `/clinics` | List clinics | Yes |
| POST | `/providers` | Create provider | Yes |
| GET | `/providers` | List providers | Yes |
| GET | `/providers/{id}` | Get provider by ID | Yes |
| PUT | `/providers/{id}` | Update provider | Yes |
| DELETE | `/providers/{id}` | Delete provider | Yes |
| POST | `/slots` | Create availability slot | Yes |
| GET | `/providers/{id}/slots` | Get provider's slots | Yes |

## Auth

All routes (except `/health`) require:
```
Authorization: Bearer <token>
```

JWT verified locally via shared secret — no call to auth-service.

## Schema

```
departments         — id, name (unique)
specialties         — id, name (unique)
clinics             — id, name, address
providers           — id, name, email (unique), user_id (plain int), department_id (FK → departments), created_at
provider_specialties — provider_id (FK), specialty_id (FK)
provider_clinics     — provider_id (FK), clinic_id (FK)
slots               — id, provider_id (FK), clinic_id (FK), start_time, end_time, is_available
                      UNIQUE (provider_id, start_time) — double-booking prevention at DB level
```

> `user_id` on providers has no FK constraint — provider-service and auth-service have isolated databases. Consistency enforced via JWT.
