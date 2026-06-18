# auth-service

Handles user registration, authentication, and role management. Issues JWT tokens consumed by all other services.

## Stack
- Python 3.12 · FastAPI · SQLAlchemy · Alembic · PostgreSQL
- bcrypt (password hashing) · python-jose (JWT) · Pydantic v2

## Running

```bash
docker-compose up --build
```

Service runs on `http://localhost:8001` — Swagger at `http://localhost:8001/docs`

## Database

- Container: `auth-db` (internal) · exposed on `localhost:5433`
- Database: `auth_db`
- Migrations: Alembic (`alembic upgrade head` from `services/auth-service/`)

## API

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| POST | `/roles` | Create a role | Yes |
| GET | `/roles` | List all roles | Yes |
| DELETE | `/roles/{id}` | Delete a role | Yes |
| POST | `/users` | Register a user | No |
| GET | `/users` | List all users | Yes |
| GET | `/users/{id}` | Get user by ID | Yes |
| PUT | `/users/{id}` | Update user | Yes |
| DELETE | `/users/{id}` | Delete user | Yes |
| POST | `/login` | Login → returns JWT | No |

## Auth Flow

```
POST /users        → register with email + password + role_id
POST /login        → returns { access_token, token_type }
```

Use the `access_token` as a Bearer token in all protected endpoints across all services.

## Schema

```
roles       — id, role_name (unique)
users       — id, email (unique), password_hash, role_id (FK → roles), created_at
```
