# API Reference — Queuemedix

Base URL: /api/v1

This document provides a detailed, per-endpoint reference derived from the current router modules and Pydantic schemas in the codebase. For concise models and full field lists, see `src/app/schemas.py`.

Authentication: Most endpoints require a Bearer access token (short-lived JWT). Use the `/auth/signin` endpoint to obtain access and refresh tokens. Some admin routes require a SUPER_ADMIN role.

---

## Authentication

### POST /api/v1/auth/register

- Description: Register a new user (patient, doctor, or hospital). Triggers email verification flow.
- Auth: Public
- Request body: RegisterUser
  - username: string
  - email: string (email)
  - role: string enum (default patient)
  - password: string (validated length/complexity)
- Response: 201
  - message: string
  - user: User (created object)

Example request body:

```json
{
	"username": "alice",
	"email": "alice@example.com",
	"role": "patient",
	"password": "S3cur3!Pass"
}
```

---

### POST /api/v1/auth/signin

- Description: Login endpoint. Returns access_token and refresh_token
- Auth: Public
- Request body: LoginData
  - username: string (or email)
  - password: string
- Response: 200
  - message: string
  - access_token: string
  - refresh_token: string

Example:

```json
{ "username": "alice", "password": "S3cur3!Pass" }
```

---

### GET /api/v1/auth/me

- Description: Get current authenticated user's details
- Auth: Bearer access token
- Response: 200 — `UserReadMe` schema (user fields + nested admin/patient/doctor/hospital profiles)

---

### POST /api/v1/auth/logout

- Description: Revoke access and refresh tokens (logout)
- Auth: Bearer access token
- Response: 200 — message

---

### GET /api/v1/auth/access_token

- Description: Exchange a refresh token for a new access token
- Auth: Uses RefreshTokenBearer as dependency (refresh token)
- Response: 200 — { access_token }

---

### Email verification / password reset endpoints

- GET /api/v1/auth/email_verification/{token} — verify account via token
- POST /api/v1/auth/password-reset — request a password reset email
- POST /api/v1/auth/password-resets/{token} — confirm password reset with new password

## Users

### GET /api/v1/users/check-username?username={username}

- Description: Check username availability
- Auth: Public
- Response: 200 { "available": true|false }

---

### GET /api/v1/users/

- Description: List all users
- Auth: SUPER_ADMIN only (require_super_admin)
- Query params: skip, limit
- Response: 200 — List[User]

---

### GET /api/v1/users/{user_id}

- Description: Get a user by id
- Auth: SUPER_ADMIN only
- Response: 200 — User

---

### DELETE /api/v1/users/{user_id}

- Description: Delete a user
- Auth: SUPER_ADMIN only
- Response: 200 — message

## Hospitals

### GET /api/v1/hospitals

- Description: List hospitals; supports search/filter in service layer
- Auth: Requires authenticated user
- Query params: skip, limit, search
- Response: 200 — List[HospitalRead]

---

### GET /api/v1/hospitals/{hospital_uid}

- Description: Get hospital by UID
- Auth: Authenticated
- Response: 200 — HospitalRead

---

### PATCH /api/v1/hospitals/{hospital_uid}/profile

- Description: Update hospital profile
- Auth: Hospital owner (current_user must be hospital user)
- Request body: HospitalProfileUpdate
- Response: 200 — `HospitalRead`

---

### GET /api/v1/hospitals/{hospital_uid}/doctors

- Description: List doctors for a hospital, optional `availability` query param
- Auth: Authenticated
- Response: 200 — List[Doctor]

---

### GET /api/v1/hospitals/{hospital_uid}/appointments?status={status}

- Description: View hospital appointments (filtered by status or ALL)
- Auth: admin/hospital/doctor
- Response: 200 — List[AppointmentRead]

---

### PATCH /api/v1/hospitals/{admin_uid}/duty

- Description: Assign duty to department admin
- Auth: hospital owner
- Request: AssignAdminDuty { notes: str }
- Response: 200 { message }

### DELETE /api/v1/hospitals/{hospital_uid}

- Description: Delete hospital
- Auth: Admin or hospital owner
- Response: 204

## Departments

### POST /api/v1/hospitals/{hospital_uid}/departments

- Description: Create department in a hospital
- Auth: admin/hospital with permission
- Request: DepartmentCreate {name}
- Response: 201 — Department

---

### GET /api/v1/departments

- Description: List departments
- Query: skip, limit, search
- Auth: Authenticated
- Response: 200 — List[Department]

---

### GET /api/v1/departments/{department_uid}

- Response: 200 — Department

### PATCH /api/v1/departments/{department_uid}

- Request: DepartmentUpdate
- Response: 202 — Department

### DELETE /api/v1/departments/{department_uid}

- Response: 204

## Patients

### PATCH /api/v1/patients/{patient_uid}

- Description: Update patient profile (owner only)
- Auth: patient owner
- Request: PatientProfileUpdate
- Response: 200 — PatientRead

---

### GET /api/v1/patients

- Description: List patients (Admins/Doctors/Hospital roles)
- Query: skip, limit, search
- Auth: Admin/Doctor/Hospital
- Response: 200 — List[PatientRead]

---

### GET /api/v1/patients/{patient_uid}

- Description: Get a patient by uid
- Auth: Admin/Doctor/Hospital or patient owner
- Response: 200 — PatientRead

---

### GET /api/v1/patients/cards/{patient_card_id}

- Description: Fetch by hospital card id
- Auth: Admin/Doctor/Hospital
- Response: 200 — PatientRead

---

### DELETE /api/v1/patients/{patient_uid}

- Description: Delete patient (Admin types or owner)
- Auth: Admin (SUPER/HOSPITAL) or patient owner
- Response: 204

## Doctors

### GET /api/v1/doctors/search?q=...&specialty=...

- Description: Search doctors (admin role)
- Auth: Admin (super/admin)
- Query params: q, specialty, hospital_id, is_available, status, page, per_page, sort_by, sort_dir
- Response: 200 — List[DoctorRead]

---

### GET /api/v1/doctors/

- Description: List doctors (SUPER_ADMIN)
- Auth: SUPER_ADMIN
- Response: 200 — List[Doctor]

---

### GET /api/v1/doctors/{doctor_id}

- Description: Get a doctor by id (doctor role) — restricted
- Auth: Doctor
- Response: 200 — DoctorRead

---

### GET /api/v1/doctors/{hospital_id}

- Description: Get pending doctors for hospital (HOSPITAL_ADMIN)
- Auth: HOSPITAL_ADMIN
- Response: 200 — List[DoctorRead]

---

### PATCH /api/v1/doctors/{doctor_id}/status

- Description: Approve/reject doctor (HOSPITAL_ADMIN)
- Body: DoctorStatus (enum)
- Response: 202 — updated doctor

---

### PATCH /api/v1/doctors/{doctor_id}/availability

- Description: Change availability (admin or doctor)
- Response: 202 — DoctorRead

### PATCH /api/v1/doctors/{doctor_id}

- Description: Update doctor profile (doctor only)
- Body: DoctorProfileUpdate
- Response: 202 — DoctorRead

## Appointments

### POST /api/v1/appointments/new_appointment?patient_uid={patient_uid}

- Description: Create a new appointment. Only patients can create.
- Auth: Patient
- Request body: AppointmentCreate
  - appointment_note: string
  - scheduled_time: datetime (ISO)
  - hospital_uid: uuid
  - department_uid: uuid
- Response: 201 — AppointmentRead
- Behavior: checks schedule conflicts, patient pending appointment, sends emails and notifications, broadcasts queue update.

Example body:

```json
{
	"appointment_note": "Flu symptoms",
	"scheduled_time": "2025-12-01T10:00:00Z",
	"hospital_uid": "<hospital-uuid>",
	"department_uid": "<department-uuid>"
}
```

---

### GET /api/v1/appointments

- Description: List appointments (SUPER_ADMIN only)
- Query: status, skip, limit
- Response: 200 — List[AppointmentRead]

---

### GET /api/v1/appointments/{patient_uid}/appointments

- Description: Get patient appointments
- Auth: Patient/Doctor/Admin checks in permissions
- Response: 200 — List[AppointmentRead]

---

### GET /api/v1/appointments/uncompleted_appointments

- Description: Get uncompleted appointments
- Auth: Authenticated
- Response: 200 — List[Appointment]

---

### GET /api/v1/appointments/pending_appointments

- Description: Get pending appointments filtered by role
- Auth: Authenticated
- Response: 200 — List[AppointmentRead]

---

### GET /api/v1/appointments/{appointment_uid}

- Description: Get appointment details
- Auth: Role checks via permissions.general_access
- Response: 200 — Appointment

---

### PATCH /api/v1/appointments/{appointment_uid}/cancel

- Description: Cancel appointment (patient only)
- Auth: appointment.patient owner
- Response: 202 — message
- Behavior: notify queue and send cancellation emails

---

### PUT /api/v1/appointments/{appointment_uid}/appointment_status

- Description: Update appointment status (doctors/admin/hospital roles per permissions)
- Body: AppointmentStatusUpdate { status: enum }
- Response: 200 — message

---

### DELETE /api/v1/appointments/{appointment_uid}/delete

- Description: Permanently delete appointment (patient owner)
- Response: 204

---

### PUT /api/v1/appointments/{appointment_uid}/reschedule

- Description: Reschedule appointment (checks availability)
- Body: RescheduleAppointment { new_time: datetime, reason: string }
- Auth: permission checks
- Response: 200 — { message, appointment }

## Admins

### GET /api/v1/admins

- Description: List admins (SUPER_ADMIN)
- Response: 200 — List[AdminRead]

---

### GET /api/v1/admins/{admin_id}

- Description: Get admin by id (SUPER_ADMIN)
- Response: 200 — AdminRead

---

### GET /api/v1/hospitals/{hospital_id}/admins

- Description: Get admins of a hospital
- Auth: SUPER_ADMIN or HOSPITAL_ADMIN with ownership checks
- Response: 200 — List[AdminRead]

---

### PUT /api/v1/admins/{admin_id}

- Description: Update admin profile
- Body: AdminProfileUpdate
- Response: 202 — AdminRead

---

### DELETE /api/v1/admins/{admin_id}

- Description: Delete admin (SUPER_ADMIN or HOSPITAL_ADMIN)
- Response: 200 — message

---

### PATCH /api/v1/appointments/{appointment_uid}/admin

- Description: Assign doctor to appointment (Admin flow)
- Body: DoctorAssign { doctor_uid }
- Response: 202 — message
- Behavior: checks doctor availability, sets doctor_uid on appointment, notifies doctor & patient

---

### PATCH /api/v1/hospitals/{hospital_uid}/admin

- Description: Approve/reject hospital application (SUPER_ADMIN)
- Body: VerifyHospital { status }
- Response: 200 — message

## Medical Records

### POST /api/v1/medical_records/{appointment_id}

- Description: Create medical record (doctor/hospital admin). Appointment IDs used to associate patient/doctor/hospital fields.
- Auth: Doctor/Hospital Admin
- Body: MedicalRecordCreate
  - patient_uid (optional — service fills from appointment)
  - doctor_uid (optional)
  - hospital_uid (optional)
  - record_type: enum
  - description: string
  - record_date: datetime
- Response: 201 — MedicalRecordRead

---

### GET /api/v1/medical_records/{hospital_id}

- Description: Get records for hospital. Admin-only access.
- Query: offset, limit
- Response: 200 — List[MedicalRecord]

---

### GET /api/v1/medical_records/{record_id}

- Description: Get a medical record by UID
- Auth: role and ownership checks
- Response: 200 — MedicalRecord

---

### GET /api/v1/medical_records/{patient_id}?hospital_id={hospital_id}

- Description: Get patient medical records for a hospital
- Response: 200 — MedicalRecord or List depending on service

---

### PUT /api/v1/medical_records/{record_id}

- Description: Update an existing medical record (doctor/hospital admin)
- Body: MedicalRecordUpdate
- Response: 200 — MedicalRecord

---

### GET /api/v1/medical_records/search/{hospital_id}

- Description: Search records by patient_uid, doctor_uid, date range, with pagination
- Response: 200 — List[MedicalRecord]

## Messages (REST and WebSockets)

### REST

- POST /api/v1/messages

  - Description: Send message (creates DB record and returns it)
  - Body: MessageCreate { receiver_uid, content }
  - Auth: Authenticated
  - Response: 201 — DataPlusMessage (message and data)

- GET /api/v1/chat/history/{other_user_id}

  - Description: Get chat history between current user and other
  - Response: 200 — List[MessageRead]

- PATCH /api/v1/messages/{message_uid}

  - Description: Edit a message (sender only)
  - Body: MessageUpdate { content }
  - Response: 200 — MessageRead

- DELETE /api/v1/messages/{message_uid}

  - Description: Delete a message (sender only)
  - Response: 204

- PATCH /api/v1/messages/{message_uid}/read_receipt
  - Description: Mark message as read (receiver only)
  - Response: 200 — MessageRead

### WebSocket endpoints

- WS /api/v1/ws/dm/{hospital_uid} — DM room (connect to receive messages for that room)
- WS /api/v1/ws/ws/notifications/{user_uid} — Notifications websocket (note router prefix includes /ws — final path resolves to `/api/v1/ws/ws/notifications/{user_uid}` in current app; clients should use `/api/v1/ws/notifications/{user_uid}` if reverse-mounted differently — check `src/__init__.py` routing). The connection manager uses channel `notifications` and room = user_uid.
- WS /api/v1/ws/appointments/{hospital_uid} — Appointment queue updates (server pushes queue on connect and on updates)
- WS /api/v1/ws/support/{session_id} — Support chat websocket; messages saved to Redis and broadcast.

## Common request/response schema examples

(Short samples — see `src/app/schemas.py` for full field lists and validations.)

UserRead (partial example):

```json
{
	"uid": "<uuid>",
	"username": "alice",
	"email": "alice@example.com",
	"role": "patient",
	"is_active": true,
	"created_at": "2025-11-17T12:00:00Z",
	"updated_at": "2025-11-17T12:00:00Z"
}
```

AppointmentRead (partial):

```json
{
	"uid": "<uuid>",
	"appointment_note": "Flu symptoms",
	"scheduled_time": "2025-12-01T10:00:00Z",
	"hospital_uid": "<uuid>",
	"department_uid": "<uuid>",
	"patient_uid": "<uuid>",
	"doctor_uid": null,
	"status": "pending",
	"created_at": "...",
	"updated_at": "..."
}
```

MedicalRecordCreate example:

```json
{
	"record_type": "prescription",
	"description": "Prescribed antibiotics",
	"record_date": "2025-11-17T12:00:00Z"
}
```

MessageCreate example:

```json
{ "receiver_uid": "<uuid>", "content": "Hello, I have a question." }
```

## Notes & caveats

- The code uses role-based permission helpers in `src/app/core/permissions.py`. Some endpoints will raise errors.NotAuthorized or RoleCheckAccess depending on the caller's role.
- The WebSocket router prefixes may appear double-mounted in code comments (e.g., router prefix `/ws` and `src/__init__.py` also including `notification_ws.router` at prefix `/api/v1`). Use the running app's docs (`/api/v1/docs`) to inspect exact final paths.
- Many endpoints rely on services to fill IDs and handle side-effects (emails, redis, websocket broadcasts). The services are defined in `src/app/services`.

---

## Full schema field tables

This section reproduces every Pydantic schema defined in `src/app/schemas.py`. For each schema the table lists field name, type, whether it's required (by schema), default value if any, and a short note where relevant (validation rules, enums, or service-populated fields).

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




