## auth-service → `auth_db`

```mermaid
erDiagram
    ROLES {
        int id PK
        string role_name "unique | admin, provider, patient, front_desk"
    }
    USERS {
        int id PK
        string email "unique, not null"
        string password_hash "not null"
        int role_id FK
        datetime created_at "default now"
    }
    ROLES ||--o{ USERS : "assigned to"
```

---

## patient-service → `patient_db`

```mermaid
erDiagram
    PATIENTS {
        int id PK
        string name "not null"
        string email
        string number "not null"
        datetime date_of_birth "not null"
        int user_id "unique | no FK — references auth_db.users"
    }
    AUDIT_LOGS {
        int id PK
        int entity_id "no FK — preserves history after delete"
        string action "not null"
        datetime timestamp "default now"
        int changed_by "user_id of who made the change"
    }
```

---

## provider-service → `provider_db`

```mermaid
erDiagram
    DEPARTMENTS {
        int id PK
        string name "unique"
    }
    SPECIALTIES {
        int id PK
        string name "unique"
    }
    CLINICS {
        int id PK
        string name "not null"
        string address
    }
    PROVIDERS {
        int id PK
        string name "not null"
        string email "unique"
        int user_id "unique | no FK — references auth_db.users"
        int department_id FK
        datetime created_at "default now"
    }
    PROVIDER_SPECIALTIES {
        int provider_id FK
        int specialty_id FK
    }
    PROVIDER_CLINICS {
        int provider_id FK
        int clinic_id FK
    }
    SLOTS {
        int id PK
        int provider_id FK
        int clinic_id FK
        datetime start_time "not null"
        datetime end_time "not null"
        boolean is_available "default true"
    }

    DEPARTMENTS ||--o{ PROVIDERS : "has"
    PROVIDERS ||--o{ PROVIDER_SPECIALTIES : "has"
    SPECIALTIES ||--o{ PROVIDER_SPECIALTIES : "has"
    PROVIDERS ||--o{ PROVIDER_CLINICS : "works at"
    CLINICS ||--o{ PROVIDER_CLINICS : "has"
    PROVIDERS ||--o{ SLOTS : "owns"
    CLINICS ||--o{ SLOTS : "hosted at"
```

> **Unique constraint on slots:** `(provider_id, start_time)` — enforced at DB level to prevent double-booking under concurrent requests.

---

## Cross-Service Relationships

```
auth_db.users.id
    │
    ├──▶ patient_db.patients.user_id   (plain int, no FK)
    │
    └──▶ provider_db.providers.user_id (plain int, no FK)
```

**Why no FK?** Postgres cannot enforce foreign keys across databases. Consistency is guaranteed by JWT — a valid token means the user exists in auth-service. No cross-service DB call needed.

---

## Appointment States *(Week 2 — appointment-service)*

```
available ──▶ requested ──▶ confirmed ──▶ complete ──▶ unavailable
                  │               │
                  ▼               ▼
              cancelled       no_show
```

`appointments` table will hold a `status` column with these values. Slot `is_available` is separate — it tracks bookability, not appointment outcome.
