# Queuemedix — Product Documentation

## Table of contents

- Overview
- Technology stack
- Architecture and components
- Quick start (local)
- Docker / Deployment
- Environment variables
- Database and migrations
- Authentication & Security
- API reference (high level)
  - Authentication
  - Users
  - Hospitals
  - Departments
  - Patients
  - Doctors
  - Appointments
  - Admins
  - Medical Records
  - Messages (REST + WebSockets)
  - Notifications (WebSocket)
  - Support chat (WebSocket)
- Data models (summary)
- Websockets and real-time flows
- Background tasks & scheduler
- Development notes & testing
- Troubleshooting
- Contributing
- Appendix: important files

---

## Overview

Queuemedix is a Medical Queueing System built with FastAPI + SQLModel that helps hospitals and practitioners manage appointments, notifications and real-time chat (DM/support). The project provides role-based access (super-admin, hospital-admin, department-admin, doctor, hospital, patient), JWT-based authentication (access + refresh tokens), asynchronous DB access with SQLAlchemy/SQLModel, Redis for short-lived tokens and Celery config for background work.

This document summarizes how the project is structured, how to run it locally or in Docker, API endpoints and expected request/response shapes, plus operational notes.

## Technology stack

- Python (project uses modern versions; repository includes a venv)
- FastAPI (HTTP + OpenAPI documentation)
- SQLModel + SQLAlchemy (async) for models and DB access
- PostgreSQL (expected) — SQLModel uses PostgreSQL UUID types in models
- Redis — used for email verification tokens and other short-lived state (also configured as Celery broker/back-end)
- Uvicorn for ASGI server
- WebSockets for real-time communication (notifications, appointment queue, direct messages, support)
- Celery / APScheduler: background jobs and periodic cleanup

Dependencies are listed in `requirements.txt`.

## Architecture and components

- `src/__init__.py` — application entrypoint. Creates `FastAPI` app, attaches lifespan init_db, registers error handlers and middlewares, and includes routers.
- `src/app/router/*.py` — HTTP API routers grouped by domain (auth, users, hospitals, patients, doctors, appointments, admins, medical_records, message, department).
- `src/app/models.py` — SQLModel models (DB schema). Includes Users, Hospital, Patient, Doctor, Appointment, MedicalRecord, Message, RefreshToken, Notification, etc.
- `src/app/schemas.py` — Pydantic models used for request/response validation and documentation.
- `src/app/services/*.py` — Business-logic layer that performs DB operations and any notifications/websocket triggers.
- `src/app/database/main.py` — async SQLAlchemy engine and sessionmaker plus `init_db()` used by app lifespan.
- `src/app/core/*` — utilities, settings, auth/token helpers, custom errors, permissions, Redis helpers, and email utils.
- `src/app/websocket/*` — connection manager and ws endpoints for real-time features.
- `migrations/` and `alembic.ini` — DB migration scaffolding.

## Quick start (local)

Prerequisites

- Python 3.11+ installed
- PostgreSQL instance
- Redis instance
- (Optional) Docker & Docker Compose

Minimal local steps:

1. Create virtualenv and activate (example using venv)

```bash
python -m venv env
# On Windows (bash):
source env/Scripts/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Provide environment variables (see next section). You can create a `.env.local` in the project root containing required keys.

4. Initialize DB (the app runs `SQLModel.metadata.create_all` on startup; for production use Alembic migrations):

```bash
uvicorn src:app --reload --host 0.0.0.0 --port 8000
```

The automatic OpenAPI docs will be available at `http://localhost:8000/api/v1/docs` and OpenAPI JSON at `/api/v1/openapi.json`.

Note: The app variable is defined at `src/__init__.py`, so `uvicorn src:app` loads it.

## Docker / Deployment

The repo includes `Dockerfile` and `docker-compose.yml` (inspect those files for services and environment wiring). Typical steps:

- Build and run with Docker Compose:

```bash
docker compose up --build
```

- Ensure DB/Redis containers are reachable and env vars used inside container are set (refer to `.env.docker` if present).

## Environment variables

The settings are loaded from `src/app/core/settings.py`. The code expects the following environment variables (use `.env.local` or `.env.docker` depending on environment):

- DATABASE_URL — e.g. `postgresql+asyncpg://user:pwd@db:5432/dbname`
- JWT_SECRET
- JWT_ALGORITHM
- EMAIL_SERVER
- EMAIL_PORT
- EMAIL_USERNAME
- EMAIL_PASSWORD
- EMAIL_FROM
- MAIL_FROM_NAME
- REDIS_URL
- DOMAIN
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB
- POSTGRES_PORT

Create a `.env.local` with these variables for local development. The `Settings` object uses `.env` by default but the module switches between `.env.local` and `.env.docker` by `ENV` variable.

## Database and migrations

- Models are declared in `src/app/models.py` using SQLModel with PostgreSQL-specific types (UUID, JSONB, Enums).
- `src/app/database/main.py` contains `init_db()` that runs `SQLModel.metadata.create_all` during app startup. For production, prefer Alembic migrations in `migrations/` and `alembic.ini` (folder included).

Typical migration flow (alembic must be configured to use the async driver):

- Generate revision: `alembic revision --autogenerate -m "message"`
- Apply: `alembic upgrade head`

(Inspect `alembic.ini` and `migrations` for the existing migration configuration in this repo.)

## Authentication & Security

- JWT-based auth using two token types: Access token and Refresh token.
- Access tokens are short-lived; refresh tokens can be used to obtain new access tokens.
- Tokens include a `jti` and `session_id`. Refresh token JTIs are stored in the `refreshtokens` table. Blacklisted access tokens are stored in `blacklistedtokens` on logout.
- Passwords are hashed with bcrypt (`passlib` used in `src/app/core/utils.py`).
- Email verification uses URL-safe tokens via itsdangerous; tokens are stored in Redis for validation.

Key helpers:

- `src/app/core/utils.py` — token creation, verification, password hashing, and URL-safe token helpers.
- `src/app/core/dependencies.py` — `AccessTokenBearer`, `RefreshTokenBearer`, `get_current_user`, `require_super_admin` and role checking.
- Error handling is centralized in `src/app/core/errors.py` which registers custom exception handlers on the FastAPI app.

## API reference (high level)

All endpoints are included on the app with prefix `/api/v1` (version string defined in `src/__init__.py`). The docs live at `/api/v1/docs`.

Notes: request and response shapes typically use classes from `src/app/schemas.py`. This file contains Pydantic models for RegisterUser, LoginData, HospitalRead, AppointmentRead, PatientRead, DoctorRead, AdminRead, MedicalRecordRead and many others. Use those schema names in your client.

### Authentication (router: `src/app/router/auth.py`)

- POST /api/v1/auth/register — Register a user (roles: patient/doctor/hospital). Body: `RegisterUser`. Triggers email verification flow.
- POST /api/v1/auth/signin — Login; returns `access_token` and `refresh_token`.
- GET /api/v1/auth/me — Return the currently authenticated user (`UserReadMe` schema).
- POST /api/v1/auth/logout — Revoke access token and refresh token session.
- GET /api/v1/auth/access_token — Exchange valid refresh token for a new access token.
- Email verification and password-reset endpoints also implemented.
- Admin signup flows (signup_link, signup via token) are present for admin invites.

Authentication details and validation reside under `src/app/core/utils.py` and `src/app/core/dependencies.py`.

### Users (router: `src/app/router/users.py`)

- GET /api/v1/users/check-username — Query param `username` to check availability.
- GET /api/v1/users/ — (Super-admin only) list users.
- GET /api/v1/users/{user_id} — (Super-admin) get user details.
- DELETE /api/v1/users/{user_id} — (Super-admin) delete a user.

### Hospitals (router: `src/app/router/hospital.py`)

- GET /api/v1/hospitals — List hospitals (filters supported in service layer).
- GET /api/v1/hospitals/{hospital_uid} — Get hospital profile.
- GET /api/v1/hospitals/{hospital_uid}/appointments — View hospital appointments (Admin/Hospital/Doctor roles)
- GET /api/v1/hospitals/{hospital_id}/doctors — List doctors for a hospital
- PATCH /api/v1/hospitals/{hospital_uid}/profile — Update hospital profile
- PATCH /api/v1/hospitals/{admin_uid}/duty — assign admin duty (notes)
- DELETE /api/v1/hospitals/{hospital_uid} — Delete a hospital (admin/hospital owner authorized)

Schemas: `HospitalProfileCreate`, `HospitalProfileUpdate`, `HospitalRead` in `src/app/schemas.py`.

### Departments (router: `src/app/router/department.py`)

- POST /api/v1/hospitals/{hospital_uid}/departments — Create department
- GET /api/v1/departments — List departments
- GET /api/v1/departments/{department_uid} — Get department
- PATCH /api/v1/departments/{department_uid} — Update
- DELETE /api/v1/departments/{department_uid} — Delete

### Patients (router: `src/app/router/patients.py`)

- PATCH /api/v1/patients/{patient_uid} — Update patient profile (patient only)
- GET /api/v1/patients — List patients (Admins/Doctors/Hospital)
- GET /api/v1/patients/{patient_uid} — Get a patient (Admin/Doctor/Hospital or owner)
- GET /api/v1/patients/cards/{patient_card_id} — Fetch by hospital card id
- DELETE /api/v1/patients/{patient_uid}

Schemas: `PatientProfileCreate`, `PatientProfileUpdate`, `PatientRead`.

### Doctors (router: `src/app/router/doctors.py`)

- GET /api/v1/doctors/search — Search doctors (admin role required)
- GET /api/v1/doctors/ — List all doctors (super-admin)
- GET /api/v1/doctors/{doctor_id} — Get a doctor (doctor role checks)
- GET /api/v1/doctors/{hospital_id} — Get pending doctors for a hospital (hospital-admin)
- PATCH /api/v1/doctors/{doctor_id}/status — Approve/reject doctor (hospital-admin)
- PATCH /api/v1/doctors/{doctor_id}/availability — Toggle availability
- PATCH /api/v1/doctors/{doctor_id} — Update doctor profile

Schemas: `DoctorProfileCreate`, `DoctorProfileUpdate`, `DoctorRead`.

### Appointments (router: `src/app/router/appointment.py`)

- POST /api/v1/appointments/new_appointment?patient_uid={patientUid} — Create new appointment. Body: `AppointmentCreate`. Only patients can create.
- GET /api/v1/appointments — List appointments (admin super-admin only with optional status filter)
- GET /api/v1/appointments/{patient_uid}/appointments — Get appointments for a patient
- GET /api/v1/appointments/uncompleted_appointments — List uncompleted appointments
- GET /api/v1/appointments/pending_appointments — Get all pending appointments (filtered for role)
- GET /api/v1/appointments/{appointment_uid} — Get appointment details
- PATCH /api/v1/appointments/{appointment_uid}/cancel — Cancel appointment (patient)
- PUT /api/v1/appointments/{appointment_uid}/appointment_status — Update appointment status
- DELETE /api/v1/appointments/{appointment_uid}/delete — Permanently delete appointment (owner)
- PUT /api/v1/appointments/{appointment_uid}/reschedule — Reschedule an appointment

Schemas: `AppointmentCreate`, `AppointmentRead`, `AppointmentStatusUpdate`, `RescheduleAppointment`.

Real-time: Appointment queue updates are broadcasted via the appointments WebSocket (see Websockets section).

### Admins (router: `src/app/router/admins.py`)

- GET /api/v1/admins — List admins (super-admin)
- GET /api/v1/admins/{admin_id} — Get admin
- GET /api/v1/hospitals/{hospital_id}/admins — Get admins for a hospital
- PUT /api/v1/admins/{admin_id} — Update admin profile
- DELETE /api/v1/admins/{admin_id} — Delete admin (super or hospital admin)
- PATCH /api/v1/appointments/{appointment_uid}/admin — Assign doctor to appointment (checks availability)
- PATCH /api/v1/hospitals/{hospital_uid}/admin — Approve/reject hospital (super-admin)

### Medical Records (router: `src/app/router/medical_records.py`)

- POST /api/v1/medical_records/{appointment_id} — Create medical record (doctor/hospital admin)
- GET /api/v1/medical_records/{hospital_id} — Get records for hospital (admin roles)
- GET /api/v1/medical_records/{record_id} — Get a record by id
- GET /api/v1/medical_records/{patient_id}?hospital_id={hospital_id} — Get patient records
- PUT /api/v1/medical_records/{record_id} — Update medical record
- GET /api/v1/medical_records/search/{hospital_id} — Search medical records with filters

Schemas: `MedicalRecordCreate`, `MedicalRecordUpdate`, `MedicalRecordRead`.

### Messages (router: `src/app/router/message.py`)

REST:

- POST /api/v1/messages — Send a message (REST). Body: `MessageCreate` (receiver_uid, content)
- GET /api/v1/chat/history/{other_user_id} — Chat history between two users
- PATCH /api/v1/messages/{message_uid} — Edit message
- DELETE /api/v1/messages/{message_uid} — Delete message
- PATCH /api/v1/messages/{message_uid}/read_receipt — Mark message as read

WebSockets:

- WS /api/v1/ws/dm/{hospital_uid} — DM room for doctor-patient; the room id is `hospital_uid` or combined sender/receiver id depending on implementation of `message` service. Clients connect to receive messages in the DM room.

The `message` service broadcasts messages to DM rooms via `ConnectionManager.broadcast`.

### Notifications (WebSocket: `src/app/websocket/notification_ws.py`)

- WS `/api/v1/ws/ws/notifications/{user_uid}` — connect to user notifications channel. The connection manager uses channel `notifications` and the room is `user_uid`.

### Support chat (WebSocket: `src/app/websocket/support_chat.py`)

- WS `/api/v1/ws/support/{session_id}` — Support chat websocket. Messages are stored briefly in Redis list `support:{session_id}` and broadcast to `support` channel room `session_id`.

## Data models (summary)

Full model definitions live in `src/app/models.py`. Key entities:

- User — base table with uid (UUID), username, email, hashed_password, role, is_active, timestamps
- Patient / Doctor / Admin / Hospital — profile tables with FK to `users.uid`
- Appointment — holds patient_uid, doctor_uid, hospital_uid, scheduled_time, status, timestamps
- MedicalRecord + MedicalRecordFile
- Message — chat messages with sender_uid and receiver_uid
- RefreshToken, BlacklistedToken — token session and revocation tracking
- Notification — stored notifications

Refer to `src/app/models.py` for exact column types and relationships. Most relationships use `selectin` loading.

## Websockets and real-time flows

- ConnectionManager (global `manager`) lives in `src/app/websocket/connection_manager.py`. It stores connections by channel and room id and supports `connect`, `disconnect`, and `broadcast(channel, room_id, message)`.
- Appointment queue: `src/app/websocket/appointment_ws.py` exposes WS `/ws/appointments/{hospital_uid}`. On connect, server sends the initial queue and future queue updates via `notify_queue_update` called by appointment services. This allows hospital staff clients to observe the real-time appointment queue.
- Notifications: `notification_ws` broadcasts new stored notifications to a user's room.
- DM messages: message sends via REST create message, service writes message row and then broadcasts to the `dm` channel using a deterministic room id. Clients subscribe to `/ws/dm/{hospital_uid}` in current implementation.
- Support: support chat persists messages to Redis and broadcasts to the support room.

Clients should maintain websocket connections and parse broadcast payloads (the code sends JSON objects containing `type` or direct message payloads containing `uid`, `title`, `body`, etc.).

## Background tasks & scheduler

- `src/__init__.py` registers a lifespan handler that runs `init_db()` at startup and sets up an `AsyncIOScheduler` to run `cleanup_job` every 24 hours. `cleanup_job` calls `delete_expired_tokens` in `src/app/services/sign_up_link.py`.
- Redis and Celery settings are available in `src/app/core/settings.py` and `src/app/core/celery.py` (Celery config present — background tasks likely elsewhere).

## Development notes & testing

- There are no tests present in the repository snapshot. Add unit tests (pytest) focusing on services and routers.
- Quick linting/formatting: add `ruff` and `black` or leverage existing project linters.
- To run the app locally using the virtualenv, ensure env vars and DB/Redis connections are correct. If DB is unreachable, the app will attempt to create tables in `init_db()`.

## Troubleshooting

- Common failure: DB connection errors. Verify `DATABASE_URL` format and network connectivity.
- Token & auth errors: JWT config (secret + algorithm) and timezone issues can cause validation failures.
- Websocket clients: ensure they are connecting to the right path and using the correct room ids. Check that WebSocket origin/CORS is allowed by middleware.

## Contributing

- Follow the repository coding style. Create feature branches, add tests for new logic and update the OpenAPI schema by annotating routers and Pydantic schemas.
- For DB schema changes use Alembic migrations instead of relying on `create_all` in production.

## Appendix: important files

- `src/__init__.py` — main FastAPI app
- `src/app/models.py` — DB models
- `src/app/schemas.py` — request/response schemas
- `src/app/router/*.py` — routers (auth, users, hospital, appointment, doctors, patients, admins, medical_records, message, department)
- `src/app/services/*.py` — business logic
- `src/app/websocket/*` — ws endpoints and connection manager
- `src/app/core/settings.py` — environment settings
- `src/app/database/main.py` — engine and `get_session`
- `migrations/` and `alembic.ini` — DB migrations

---

## Full schema field tables (embedded)

The following tables reproduce the Pydantic schemas defined in `src/app/schemas.py`. They list every field, type, whether it's required, default value (if any), and short notes about validation or special behavior.

### UserBase

| Field    |            Type | Required | Default             | Notes                                          |
| -------- | --------------: | -------: | ------------------- | ---------------------------------------------- |
| username |           `str` |      yes | -                   | unique in DB (enforced by service)             |
| email    | `EmailStrLower` |      yes | -                   | email string, normalized to lower-case         |
| role     |     `UserRoles` |       no | `UserRoles.PATIENT` | enum: `admin`, `doctor`, `hospital`, `patient` |

### RegisterUser

| Field    |            Type | Required | Default             | Notes                                                            |
| -------- | --------------: | -------: | ------------------- | ---------------------------------------------------------------- |
| username |           `str` |      yes | -                   | same as UserBase                                                 |
| email    | `EmailStrLower` |      yes | -                   | same as UserBase                                                 |
| role     |     `UserRoles` |       no | `UserRoles.PATIENT` | same as UserBase                                                 |
| password |           `str` |      yes | -                   | validated: >=8 chars, contains digit, lower, upper, special char |

### RegisterAdminUser

| Field    |            Type | Required | Default           | Notes                                    |
| -------- | --------------: | -------: | ----------------- | ---------------------------------------- |
| username |           `str` |      yes | -                 | admin-only signup flows                  |
| email    | `EmailStrLower` |      yes | -                 |
| role     |     `UserRoles` |       no | `UserRoles.ADMIN` | always admin by default                  |
| password |           `str` |      yes | -                 | same password validation as RegisterUser |

### UserRead

| Field      |            Type | Required | Default | Notes             |
| ---------- | --------------: | -------: | ------- | ----------------- |
| uid        |     `uuid.UUID` |      yes | -       | DB primary UUID   |
| username   |           `str` |      yes | -       |
| email      | `EmailStrLower` |      yes | -       |
| role       |     `UserRoles` |      yes | -       |
| is_active  |          `bool` |       no | `False` | activation status |
| created_at |      `datetime` |      yes | -       |
| updated_at |      `datetime` |      yes | -       |

### HospitalBase

| Field               |           Type | Required | Default                | Notes                                |
| ------------------- | -------------: | -------: | ---------------------- | ------------------------------------ |
| hospital_name       |          `str` |      yes | -                      | unique in DB                         |
| full_address        |          `str` |      yes | -                      |
| state               |          `str` |      yes | -                      |
| website             |          `str` |       no | `None`                 |
| license_number      |          `str` |      yes | -                      | unique                               |
| phone_number        |          `str` |      yes | -                      |
| registration_number |          `str` |      yes | -                      | unique                               |
| ownership_type      | `HospitalType` |       no | `HospitalType.PRIVATE` | enum: `private`, `government`, `ngo` |
| hospital_ceo        |          `str` |      yes | -                      |

### HospitalProfileCreate

Same fields as `HospitalBase` (all required except `website`).

### HospitalProfileUpdate

| Field               |           Type | Required | Default | Notes |
| ------------------- | -------------: | -------: | ------- | ----- |
| hospital_name       |          `str` |       no | `None`  |
| full_address        |          `str` |       no | `None`  |
| state               |          `str` |       no | `None`  |
| website             |          `str` |       no | `None`  |
| license_number      |          `str` |       no | `None`  |
| phone_number        |          `str` |       no | `None`  |
| registration_number |          `str` |       no | `None`  |
| ownership_type      | `HospitalType` |       no | `None`  |
| hospital_ceo        |          `str` |       no | `None`  |

### VerifyHospital

| Field  |             Type | Required | Default | Notes                                        |
| ------ | ---------------: | -------: | ------- | -------------------------------------------- |
| status | `HospitalStatus` |      yes | -       | enum: `under_review`, `approved`, `rejected` |

### HospitalRead

| Field               |             Type | Required | Default                       | Notes           |
| ------------------- | ---------------: | -------: | ----------------------------- | --------------- |
| hospital_name       |            `str` |      yes | -                             |
| full_address        |            `str` |      yes | -                             |
| state               |            `str` |      yes | -                             |
| website             |            `str` |       no | `None`                        |
| license_number      |            `str` |      yes | -                             |
| phone_number        |            `str` |      yes | -                             |
| registration_number |            `str` |      yes | -                             |
| ownership_type      |   `HospitalType` |       no | `HospitalType.PRIVATE`        |
| hospital_ceo        |            `str` |      yes | -                             |
| uid                 |      `uuid.UUID` |      yes | -                             | hospital uid    |
| user_uid            |      `uuid.UUID` |      yes | -                             | FK -> users.uid |
| is_verified         |           `bool` |       no | `False`                       |
| status              | `HospitalStatus` |       no | `HospitalStatus.UNDER_REVIEW` |

### PatientBase

| Field                          |   Type | Required | Default | Notes |
| ------------------------------ | -----: | -------: | ------- | ----- |
| full_name                      |  `str` |      yes | -       |
| hospital_card_id               |  `str` |      yes | -       |
| phone_number                   |  `str` |      yes | -       |
| date_of_birth                  | `date` |      yes | -       |
| gender                         |  `str` |      yes | -       |
| country                        |  `str` |      yes | -       |
| state_of_residence             |  `str` |      yes | -       |
| home_address                   |  `str` |      yes | -       |
| blood_type                     |  `str` |      yes | -       |
| emergency_contact_full_name    |  `str` |      yes | -       |
| emergency_contact_phone_number |  `str` |      yes | -       |

### PatientProfileCreate

Same as `PatientBase`.

### PatientProfileUpdate

All `PatientBase` fields marked optional; default `None` when not provided.

### PatientRead

| Field                    |        Type | Required | Default | Notes |
| ------------------------ | ----------: | -------: | ------- | ----- |
| (all PatientBase fields) |             |          |         |
| uid                      | `uuid.UUID` |      yes | -       |
| user_uid                 | `uuid.UUID` |      yes | -       |

### DoctorBase

| Field              |        Type | Required | Default | Notes  |
| ------------------ | ----------: | -------: | ------- | ------ |
| full_name          |       `str` |      yes | -       |
| phone_number       |       `str` |      yes | -       |
| date_of_birth      |      `date` |       no | `None`  |
| gender             |       `str` |      yes | -       |
| country            |       `str` |      yes | -       |
| state_of_residence |       `str` |      yes | -       |
| home_address       |       `str` |      yes | -       |
| hospital_uid       | `uuid.UUID` |       no | `None`  |
| department_uid     | `uuid.UUID` |       no | `None`  |
| license_number     |       `str` |      yes | -       | unique |
| specialization     |       `str` |      yes | -       |
| qualification      |       `str` |      yes | -       |
| bio                |       `str` |       no | `None`  |
| is_available       |      `bool` |       no | `True`  |

### DoctorProfileCreate

Same fields as `DoctorBase`.

### DoctorProfileUpdate

All `DoctorBase` fields optional + `years_of_experience` (Optional[int]).

### DoctorAssign

| Field      |  Type | Required | Default | Notes                          |
| ---------- | ----: | -------: | ------- | ------------------------------ |
| doctor_uid | `str` |      yes | -       | UID string of doctor to assign |

### DoctorRead

| Field                   |           Type | Required | Default                     | Notes |
| ----------------------- | -------------: | -------: | --------------------------- | ----- |
| (all DoctorBase fields) |                |          |                             |
| uid                     |    `uuid.UUID` |      yes | -                           |
| status                  | `DoctorStatus` |       no | `DoctorStatus.UNDER_REVIEW` |
| user_uid                |    `uuid.UUID` |      yes | -                           |
| department_uid          |    `uuid.UUID` |       no | `None`                      |

### AdminBase

| Field          |        Type | Required | Default                    | Notes |
| -------------- | ----------: | -------: | -------------------------- | ----- |
| full_name      |       `str` |      yes | -                          |
| hospital_uid   | `uuid.UUID` |       no | `None`                     |
| admin_type     | `AdminType` |       no | `AdminType.HOSPITAL_ADMIN` |
| department_uid | `uuid.UUID` |       no | `None`                     |

### AdminProfileCreate

Same as `AdminBase`.

### AdminProfileUpdate

All AdminBase fields, but `admin_type` can be `AdminTypeUpdate` and `notes: Optional[str]` included.

### AssignAdminDuty

| Field |  Type | Required | Default | Notes                     |
| ----- | ----: | -------: | ------- | ------------------------- |
| notes | `str` |      yes | -       | free text describing duty |

### AdminRead

| Field              |        Type | Required | Default | Notes |
| ------------------ | ----------: | -------: | ------- | ----- |
| (AdminBase fields) |             |          |         |
| uid                | `uuid.UUID` |      yes | -       |
| user_uid           | `uuid.UUID` |      yes | -       |
| notes              |       `str` |       no | `None`  |

### AppointmentBase

| Field            |        Type | Required | Default | Notes |
| ---------------- | ----------: | -------: | ------- | ----- |
| appointment_note |       `str` |      yes | -       |
| scheduled_time   |  `datetime` |      yes | -       |
| hospital_uid     | `uuid.UUID` |      yes | -       |
| department_uid   | `uuid.UUID` |      yes | -       |

### AppointmentCreate

Same as `AppointmentBase`.

### AppointmentCancel

| Field               |  Type | Required | Default | Notes |
| ------------------- | ----: | -------: | ------- | ----- |
| cancellation_reason | `str` |      yes | -       |

### AppointmentStatusUpdate

| Field  |                Type | Required | Default | Notes                                                        |
| ------ | ------------------: | -------: | ------- | ------------------------------------------------------------ |
| status | `AppointmentStatus` |      yes | -       | enum: pending, completed, canceled, in_progress, rescheduled |

### RescheduleAppointment

| Field    |       Type | Required | Default | Notes |
| -------- | ---------: | -------: | ------- | ----- |
| new_time | `datetime` |      yes | -       |
| reason   |      `str` |      yes | -       |

### AppointmentRead

| Field                    |                Type | Required | Default                     | Notes |
| ------------------------ | ------------------: | -------: | --------------------------- | ----- |
| (AppointmentBase fields) |                     |          |                             |
| uid                      |         `uuid.UUID` |      yes | -                           |
| patient_uid              |         `uuid.UUID` |      yes | -                           |
| doctor_uid               |         `uuid.UUID` |       no | `None`                      |
| status                   | `AppointmentStatus` |       no | `AppointmentStatus.PENDING` |
| rescheduled_from         |          `datetime` |       no | `None`                      |
| check_in_time            |          `datetime` |       no | `None`                      |
| completed_time           |          `datetime` |       no | `None`                      |
| created_at               |          `datetime` |      yes | -                           |
| updated_at               |          `datetime` |      yes | -                           |

### DepartmentCreate

| Field |  Type | Required | Default | Notes |
| ----- | ----: | -------: | ------- | ----- |
| name  | `str` |      yes | -       |

### DepartmentUpdate

| Field |  Type | Required | Default | Notes |
| ----- | ----: | -------: | ------- | ----- |
| name  | `str` |       no | `None`  |

### DepartmentRead

| Field           |        Type | Required | Default | Notes                                             |
| --------------- | ----------: | -------: | ------- | ------------------------------------------------- |
| uid             | `uuid.UUID` |      yes | -       |
| name            |       `str` |      yes | -       |
| hospital_uid    | `uuid.UUID` |      yes | -       |
| appointment_uid | `uuid.UUID` |      yes | -       | (note: field name in schema `appointment_uid`)    |
| doctor_iud      | `uuid.UUID` |      yes | -       | (note: schema uses `doctor_iud` typo in original) |
| created_at      |  `datetime` |      yes | -       |
| updated_at      |  `datetime` |      yes | -       |

### MedicalRecordCreate

| Field        |         Type | Required | Default                   | Notes                                             |
| ------------ | -----------: | -------: | ------------------------- | ------------------------------------------------- |
| patient_uid  |  `uuid.UUID` |       no | `None`                    | service will populate from appointment if omitted |
| doctor_uid   |  `uuid.UUID` |       no | `None`                    | same as above                                     |
| hospital_uid |  `uuid.UUID` |       no | `None`                    | same as above                                     |
| record_type  | `RecordType` |       no | `RecordType.PRESCRIPTION` | enum: diagnosis, lab_result, prescription, note   |
| description  |        `str` |      yes | -                         |
| record_date  |   `datetime` |      yes | -                         |

### MedicalRecordUpdate

| Field       |         Type | Required | Default | Notes |
| ----------- | -----------: | -------: | ------- | ----- |
| record_type | `RecordType` |       no | `None`  |
| description |        `str` |       no | `None`  |
| record_date |   `datetime` |       no | `None`  |

### MedicalRecordRead

| Field        |         Type | Required | Default | Notes |
| ------------ | -----------: | -------: | ------- | ----- |
| uid          |  `uuid.UUID` |      yes | -       |
| patient_uid  |  `uuid.UUID` |      yes | -       |
| doctor_uid   |  `uuid.UUID` |      yes | -       |
| hospital_uid |  `uuid.UUID` |       no | `None`  |
| record_type  | `RecordType` |      yes | -       |
| description  |        `str` |      yes | -       |
| record_date  |   `datetime` |      yes | -       |
| created_at   |   `datetime` |      yes | -       |
| updated_at   |   `datetime` |      yes | -       |

### MessageCreate

| Field        |        Type | Required | Default | Notes |
| ------------ | ----------: | -------: | ------- | ----- |
| receiver_uid | `uuid.UUID` |      yes | -       |
| content      |       `str` |      yes | -       |

### MessageUpdate

| Field   |  Type | Required | Default | Notes |
| ------- | ----: | -------: | ------- | ----- |
| content | `str` |       no | `None`  |

### MessageMarkAsRead

| Field   |   Type | Required | Default | Notes |
| ------- | -----: | -------: | ------- | ----- |
| is_read | `bool` |       no | `True`  |

### MessageRead

| Field        |        Type | Required | Default | Notes |
| ------------ | ----------: | -------: | ------- | ----- |
| uid          | `uuid.UUID` |      yes | -       |
| sender_uid   | `uuid.UUID` |      yes | -       |
| receiver_uid | `uuid.UUID` |      yes | -       |
| content      |       `str` |      yes | -       |
| timestamp    |  `datetime` |      yes | -       |
| is_read      |      `bool` |       no | `False` |

### LoginData

| Field    |  Type | Required | Default | Notes                                       |
| -------- | ----: | -------: | ------- | ------------------------------------------- |
| username | `str` |      yes | -       | normalized to lowercase if looks like email |
| password | `str` |      yes | -       |

### EmailModel

| Field   |        Type | Required | Default | Notes                             |
| ------- | ----------: | -------: | ------- | --------------------------------- |
| mail_to | `List[str]` |      yes | -       | list of recipient email addresses |

### PasswordResetRequest

| Field         |       Type | Required | Default | Notes |
| ------------- | ---------: | -------: | ------- | ----- |
| email_address | `EmailStr` |      yes | -       |

### ConfirmPasswordReset

| Field            |  Type | Required | Default | Notes |
| ---------------- | ----: | -------: | ------- | ----- |
| new_password     | `str` |      yes | -       |
| confirm_password | `str` |      yes | -       |

### UserReadMe

| Field      |                     Type | Required | Default | Notes |
| ---------- | -----------------------: | -------: | ------- | ----- |
| uid        |              `uuid.UUID` |      yes | -       |
| username   |                    `str` |      yes | -       |
| email      |          `EmailStrLower` |      yes | -       |
| role       |              `UserRoles` |      yes | -       |
| is_active  |                   `bool` |       no | `False` |
| created_at |               `datetime` |      yes | -       |
| updated_at |               `datetime` |      yes | -       |
| admin      |    `Optional[AdminRead]` |       no | `None`  |
| patient    |  `Optional[PatientRead]` |       no | `None`  |
| doctor     |   `Optional[DoctorRead]` |       no | `None`  |
| hospital   | `Optional[HospitalRead]` |       no | `None`  |

### DataPlusMessage

| Field   |          Type | Required | Default | Notes |
| ------- | ------------: | -------: | ------- | ----- |
| message |         `str` |      yes | -       |
| data    | `MessageRead` |      yes | -       |

---

