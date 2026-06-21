import sqlalchemy.dialects.postgresql as pg
import uuid
from sqlmodel import SQLModel, Field, Relationship, ForeignKey, Column
from sqlalchemy.orm import Mapped
from sqlalchemy import Integer, String, DateTime, Enum as pgEnum, Text
from datetime import datetime, timezone, date
from enum import Enum
from typing import Optional, List


class UserRoles(str, Enum):
    ADMIN = "admin"
    PRACTITIONER = "practitioner"
    HOSPITAL = "hospital"
    PATIENT = "patient"


class AdminType(str, Enum):
    SUPER_ADMIN = "super_admin"
    HOSPITAL_ADMIN = "hospital_admin"
    DEPARTMENT_ADMIN = "dept_admin"

class AdminTypeUpdate(str, Enum):
    HOSPITAL_ADMIN = "hospital_admin"
    DEPARTMENT_ADMIN = "dept_admin"

# Enum for Appointment Status


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"
    IN_PROGRESS = "in_progress"
    RESCHEDULED = "rescheduled"
    MISSED = "missed"


class ViewAppointmentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"
    IN_PROGRESS = "in_progress"
    RESCHEDULED = "rescheduled"
    MISSED = "missed"
    ALL = "all"


class PractitionerStatus(str, Enum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class HospitalStatus(str, Enum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

# Enum for Hospital Ownership type


class HospitalType(str, Enum):
    PRIVATE = "private"
    GOVERNMENT = "government"
    NGO = "ngo"


class RecordType(str, Enum):
    DIAGNOSIS = "diagnosis"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    CLINICAL_NOTE = "clinical_note"
    IMAGING_REPORT = "imaging_report"
    DISCHARGE_SUMMARY = "discharge_summary"

class QueueEntryStatus(str, Enum):
    WAITING = "waiting"
    CALLED = "called"
    SERVING = "serving"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    LEFT = "left"

class PractitionerType(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    PHARMACIST = "pharmacist"
    LAB_SCIENTIST = "lab_scientist"
    PHYSIOTHERAPIST = "physiotherapist"


class User(SQLModel, table=True):
    __tablename__ = "users" # type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    username: str = Field(sa_column=Column(
        String, nullable=False, unique=True))
    email: str = Field(sa_column=Column(
        String, unique=True, nullable=False, index=True))
    profile_picture: Optional[str] = Field(default=None, sa_column=Column(
        String, nullable=True))
    hashed_password: str = Field(exclude=True)
    role: UserRoles = Field(sa_column=Column(
        pgEnum(UserRoles, values_callable=lambda enum: [e.value for e in enum], name="user_role"), nullable=False))
    is_active: bool = Field(
        default=False, sa_column=Column(pg.BOOLEAN, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    def __repr__(self):
        return f"<User uid={self.uid}, username={self.username}, email={self.email}>"

    # Relationships
    sent_messages: List["Message"] = Relationship(
        back_populates="sender", sa_relationship_kwargs={"foreign_keys": "[Message.sender_uid]"})
    received_messages: List["Message"] = Relationship(
        back_populates="receiver", sa_relationship_kwargs={"foreign_keys": "[Message.receiver_uid]"})
    hospital: Mapped["Hospital"] | None = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    admin: Optional["Admin"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    patient: Optional["Patient"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    practitioner: Mapped["Practitioner"] | None = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    notifications: List["Notification"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    ratings: List["HospitalRating"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

# Hospital Model


class Hospital(SQLModel, table=True):
    __tablename__ = "hospitals" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    hospital_name: str = Field(default=None, sa_column=Column(
        String, unique=True, nullable=False))
    full_address: str = Field(default=None)
    state: str = Field(default=None)
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    website: Optional[str] = Field(default=None)
    about: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    license_number: str = Field(default=None, sa_column=Column(
        String, unique=True, nullable=False))
    phone_number: str = Field(default=None)
    registration_number: str = Field(
        default=None, sa_column=Column(String, unique=True, nullable=False))
    ownership_type: HospitalType = Field(default=HospitalType.PRIVATE, sa_column=Column(
        pgEnum(HospitalType, name="hospital_type", create_type=True), nullable=False))
    status: HospitalStatus = Field(default=HospitalStatus.UNDER_REVIEW, sa_column=Column(
        pgEnum(HospitalStatus, values_callable=lambda enum: [e.value for e in enum], name="hospital_status"), nullable=False))
    hospital_ceo: str = Field(default=None)
    average_rating: float = Field(default=0.0, sa_column=Column(pg.NUMERIC(2,1), nullable=False, default=0.0))
    is_verified: bool = Field(
        default=False, sa_column=Column(pg.BOOLEAN, nullable=False))
    cover_image: Optional[str] = Field(default=None, sa_column=Column(
        String, nullable=True))

    def __repr__(self):
        return f"<Hospital uid={self.uid}, hospital_name={self.hospital_name}>"

    # Relationship
    user: Mapped["User"] = Relationship(
        back_populates="hospital", sa_relationship_kwargs={"lazy": "selectin"})
    practitioner: List["Practitioner"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                          "lazy": "selectin"}, passive_deletes=True)
    admin: List["Admin"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                        "lazy": "selectin"}, passive_deletes=True)
    appointment: List["Appointment"] = Relationship(
        back_populates="hospital", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    department: List["Department"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                                  "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    medical_record: List["MedicalRecord"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                                         "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    ratings: List["HospitalRating"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                                          "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    queues: List["Queue"] = Relationship(
        back_populates="hospital", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)



# Patient Model
class Patient(SQLModel, table=True):
    __tablename__ = "patients" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    first_name: str = Field(default=None)
    middle_name: Optional[str] = Field(default=None)
    last_name: str = Field(default=None)
    hospital_card_id: str = Field(default=None, nullable=True)
    phone_number: str = Field(default=None)
    date_of_birth: Optional[date] = Field(default=None)
    gender: str = Field(default=None)
    country: str = Field(default=None)
    state_of_residence: str = Field(default=None)
    home_address: str = Field(default=None)
    blood_type: str = Field(default=None)
    emergency_contact_full_name: str = Field(default=None)
    emergency_contact_phone_number: str = Field(default=None)
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))

    def __repr__(self):
        return f"<Patient uid= {self.uid}, Patient's first_Name= {self.first_name}, Patient's last_name= {self.last_name}>"

    # Relationship
    user: "User" = Relationship(
        back_populates="patient", sa_relationship_kwargs={"lazy": "selectin"})
    appointment: List["Appointment"] = Relationship(
        back_populates="patient", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    medical_record: List["MedicalRecord"] = Relationship(back_populates="patient", sa_relationship_kwargs={
                                                         "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    queue_entries: List["QueueEntry"] = Relationship(
        back_populates="patient", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)


# Hospital Ratings Model
class HospitalRating(SQLModel, table=True):
    __tablename__ = "hospital_ratings" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    hospital_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "hospitals.uid", ondelete="CASCADE"), nullable=False, index=True))
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    rating: float = Field(sa_column=Column(pg.NUMERIC(2,1), nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    )

    hospital: "Hospital" = Relationship(back_populates="ratings", sa_relationship_kwargs={"lazy": "selectin"})
    user: "User" = Relationship(back_populates="ratings", sa_relationship_kwargs={"lazy": "selectin"})

# Practitioner Model
class Practitioner(SQLModel, table=True):
    __tablename__ = "practitioners" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    first_name: str = Field(default=None)
    middle_name: Optional[str] = Field(default=None)
    last_name: str = Field(default=None)
    phone_number: str = Field(default=None)
    date_of_birth: Optional[date] = Field(default=None)
    gender: str = Field(default=None)
    country: str = Field(default=None)
    state_of_residence: str = Field(default=None)
    home_address: str = Field(default=None)
    practitioner_type: PractitionerType = Field(default=PractitionerType.DOCTOR, sa_column=Column(pgEnum(PractitionerType, values_callable=lambda enum: [e.value for e in enum], name="practitioner_type"), nullable=False))
    hospital_uid: Optional[uuid.UUID] = Field(default=None, sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("hospitals.uid", ondelete="CASCADE"), nullable=True, index=True))
    department_uid: Optional[uuid.UUID] = Field(default=None, sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("departments.uid", ondelete="CASCADE"), nullable=True, index=True))
    license_number: str = Field(default=None, sa_column=Column(
        String, unique=True, nullable=False))
    specialization: str = Field(default=None)
    qualification: str = Field(default=None)
    bio: Optional[str] = Field(default=None)
    status: PractitionerStatus = Field(default=PractitionerStatus.UNDER_REVIEW, sa_column=Column(
        pgEnum(PractitionerStatus, values_callable=lambda enum: [e.value for e in enum], name="practitioner_status"), nullable=False))
    is_available: bool = Field(
        default=False, sa_column=Column(pg.BOOLEAN, nullable=False))
    years_of_experience: int = Field(default=None)
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))

    def __repr__(self):
        return f"<Pracitioner uid={self.uid}, Practitioner first_name={self.first_name}, Practitioner's last_name={self.last_name}>"

    # Relationship
    user: Mapped["User"] = Relationship(
        back_populates="practitioner", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: Mapped["Hospital"] = Relationship(
        back_populates="practitioner", sa_relationship_kwargs={"lazy": "selectin"})
    appointment: Mapped[List["Appointment"]] = Relationship(
        back_populates="practitioner", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    department: Mapped["Department"] = Relationship(
        back_populates="practitioners", sa_relationship_kwargs={"lazy": "selectin"})
    medical_record: Mapped[List["MedicalRecord"]] = Relationship(
        back_populates="practitioner", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)


# Admin Model
class Admin(SQLModel, table=True):
    __tablename__ = "admins" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    first_name: str = Field(default=None)
    middle_name: Optional[str] = Field(default=None)
    last_name: str = Field(default=None)
    hospital_uid: Optional[uuid.UUID] = Field(default=None, sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("hospitals.uid", ondelete="CASCADE"), nullable=True, index=True))
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    admin_type: AdminType = Field(sa_column=Column(
        pgEnum(AdminType, values_callable=lambda enum: [e.value for e in enum], name="admin_type"), nullable=False))
    department_uid: Optional[uuid.UUID] = Field(default=None, sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("departments.uid", ondelete="CASCADE"), nullable=True, index=True))
    notes: Optional[str] = None

    def __repr__(self):
        return f"<ADMIN: uid={self.uid}, First Name={self.first_name}, Last Name={self.last_name} Admin Type={self.admin_type}>"

    # Relationships
    user: "User" = Relationship(
        back_populates="admin", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="admin", sa_relationship_kwargs={"lazy": "selectin"})
    department: Optional["Department"] = Relationship(
        back_populates="admin", sa_relationship_kwargs={"lazy": "selectin"})

# Appointment model


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    patient_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "patients.uid", ondelete="CASCADE"), nullable=False, index=True))
    hospital_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "hospitals.uid", ondelete="CASCADE"), nullable=False, index=True))
    appointment_note: str
    scheduled_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True))
    check_in_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True))
    completed_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True))
    cancellation_reason: Optional[str] = None
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING, sa_column=Column(pgEnum(AppointmentStatus, values_callable=lambda enum: [e.value for e in enum], name="appointment_status"), nullable=False))
    practitioner_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "practitioners.uid", ondelete="CASCADE"), nullable=True, index=True))
    department_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "departments.uid", ondelete="CASCADE"), nullable=False, index=True))
    rescheduled_from: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    def __repr__(self):
        return f"<Appointment uid={self.uid}, Patient uid={self.patient_uid}, Practitioner uid={self.practitioner_uid}, Status={self.status}>"

    # Relationship
    patient: "Patient" = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"})
    practitioner: "Practitioner" = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"})
    department: "Department" = Relationship(
        back_populates="appointments", sa_relationship_kwargs={"lazy": "selectin"})
    reschedule_history: List["RescheduleHistory"] = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    queue_entries: Optional["QueueEntry"] = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)


# Appointment Reschedule History
class RescheduleHistory(SQLModel, table=True):
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    appointment_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "appointments.uid", ondelete="CASCADE"), nullable=False, index=True, unique=False))
    old_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    new_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    reason: Optional[str] = Field(default=None, max_length=255)
    rescheduled_by: Optional[uuid.UUID] = Field(
        default=None)  # Could be doctor/hospital admin ID
    rescheduled_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    # Optional relationships
    appointment: Optional["Appointment"] = Relationship(
        back_populates="reschedule_history", sa_relationship_kwargs={"lazy": "selectin"})

# Hospital Departments


class Department(SQLModel, table=True):
    __tablename__ = "departments" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    hospital_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "hospitals.uid", ondelete="CASCADE"), nullable=False, index=True))
    name: str = Field(sa_column=Column(
        String, unique=True, index=True, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    def __repr__(self):
        return f"Department uid={self.uid}, Hospital uid={self.hospital_uid}, Department Name={self.name}"

    # Relationships
    hospital: "Hospital" = Relationship(
        back_populates="department", sa_relationship_kwargs={"lazy": "selectin"})
    admin: List["Admin"] = Relationship(
        back_populates="department", sa_relationship_kwargs={"lazy": "selectin"})
    practitioners: List["Practitioner"] = Relationship(
        back_populates="department", sa_relationship_kwargs={"lazy": "selectin"})
    appointments: List["Appointment"] = Relationship(
        back_populates="department", sa_relationship_kwargs={"lazy": "selectin"})
    

# Medical Record Model


class MedicalRecord(SQLModel, table=True):
    __tablename__ = "medical_records" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    patient_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "patients.uid", ondelete="CASCADE"), nullable=False, index=True))
    practitioner_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "practitioners.uid", ondelete="CASCADE"), nullable=False, index=True))
    hospital_uid: Optional[uuid.UUID] = Field(sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("hospitals.uid", ondelete="CASCADE"), nullable=True, index=True))
    record_type: RecordType = Field(default=RecordType.PRESCRIPTION, sa_column=Column(
        pgEnum(RecordType, values_callable=lambda enum: [e.value for e in enum], name="record_type"), nullable=True))
    description: str
    record_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    def __repr__(self):
        return f"<Medical Record uid={self.uid}, Patient uid={self.patient_uid}, Practitioner uid={self.practitioner_uid}, Hospital uid={self.hospital_uid}, Record Type={self.record_type}>"

    # Relationships
    files: List["MedicalRecordFile"] = Relationship(back_populates="medical_record", sa_relationship_kwargs={
                                                    "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    patient: "Patient" = Relationship(
        back_populates="medical_record", sa_relationship_kwargs={"lazy": "selectin"})
    practitioner: "Practitioner" = Relationship(
        back_populates="medical_record", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="medical_record", sa_relationship_kwargs={"lazy": "selectin"})


class MedicalRecordFile(SQLModel, table=True):
    __tablename__ = "medical_record_files" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    record_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "medical_records.uid", ondelete="CASCADE"), nullable=False, index=True))

    file_name: str
    file_url: str  # S3/GCP/local storage path
    file_type: str  # e.g. pdf, jpg, png, docx
    uploaded_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    def __repr__(self):
        return f"<MR File uid={self.uid}, Record uid ={self.record_uid}, File name={self.file_name}, File type={self.file_type}>"

    # Relationship
    medical_record: Optional[MedicalRecord] = Relationship(
        back_populates="files", sa_relationship_kwargs={"lazy": "selectin"})


# Signup Link - Table to store generated tokens for Admins/Practitioners signup links.
class SignupLink(SQLModel, table=True):
    __tablename__ = "signup_links" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    token: str = Field(sa_column=Column(String, unique=True, index=True))
    email: str = Field(sa_column=Column(String, nullable=False))
    hospital_uid: uuid.UUID = Field(sa_column=Column(String, nullable=False))
    department_uid: uuid.UUID = Field(sa_column=Column(String, nullable=True))
    admin_type: AdminType = Field(default=AdminType.HOSPITAL_ADMIN, sa_column=Column(
        pgEnum(AdminType, values_callable=lambda enum: [e.value for e in enum], name="admin_type"), nullable=False))
    practitioner_type: PractitionerType = Field(default=PractitionerType.DOCTOR, sa_column=Column(pgEnum(PractitionerType, values_callable=lambda enum: [e.value for e in enum], name="practitioner_type"), nullable=False))
    notes: Optional[str] = None
    is_used: bool = Field(default=False)
    created_at: datetime = Field(default=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))

    def __repr__(self):
        return f"<SignupLink: uid={self.uid}, email= {self.email}, is_used={self.is_used}>"


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    email: str
    token: str = Field(unique=True, nullable=False)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    is_used: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )


class Message(SQLModel, table=True):
    __tablename__ = "messages" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    sender_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    receiver_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    content: str
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    is_read: bool = Field(default=False)
    is_edited: bool = Field(default=False)

    def __repr__(self):
        return f"<Message uid={self.uid}, sender's id={self.sender_uid}, receiver's uid={self.receiver_uid}, content={self.content}>"

    # Relationships
    sender: "User" = Relationship(
        back_populates="sent_messages",
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Message.sender_uid]",  # must be string reference
            "passive_deletes": True
        }
    )
    receiver: "User" = Relationship(
        back_populates="received_messages",
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Message.receiver_uid]",
            "passive_deletes": True
        }
    )


class BlacklistedToken(SQLModel, table=True):
    __tablename__ = "blacklistedtokens" #type: ignore

    uid: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    token_jti: str = Field(sa_column=Column(String, unique=True))
    session_id: str = Field(sa_column=Column(String, index=True, unique=True))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refreshtokens" #type: ignore

    uid: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    jti: str = Field(sa_column=Column(String, index=True, unique=True))
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    session_id: str = Field(sa_column=Column(String, index=True, unique=True))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    revoked: bool = Field(default=False)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications" #type: ignore

    uid: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    title: str
    body: str
    data: dict = Field(default_factory=dict,
                       sa_column=Column(pg.JSONB, nullable=False))
    is_read: bool = Field(default=False)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    user: "User" = Relationship(
        back_populates="notifications", sa_relationship_kwargs={"lazy": "selectin"})


class Queue(SQLModel, table=True):
    __tablename__ = "queues" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    name: str
    hospital_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "hospitals.uid", ondelete="CASCADE"), nullable=False, index=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
    
    def __repr__(self):
        return f"<Queue uid={self.uid}, Hospital uid={self.hospital_uid}, >"
    

    # Relationship
    hospital: "Hospital" = Relationship(
        back_populates="queues", sa_relationship_kwargs={"lazy": "selectin"})
    queue_entries: List["QueueEntry"] = Relationship(
        back_populates="queues", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)


class QueueEntry(SQLModel, table=True):
    __tablename__ = "queue_entries" #type: ignore

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    queue_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "queues.uid", ondelete="CASCADE"), nullable=False, index=True))
    queue_number: int    
    status: QueueEntryStatus = Field(default=QueueEntryStatus.WAITING, sa_column=Column(
        pgEnum(QueueEntryStatus, values_callable=lambda enum: [e.value for e in enum], name="queue_status"), nullable=False))
    patient_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "patients.uid", ondelete="CASCADE"), nullable=True, index=True))
    appointment_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "appointments.uid", ondelete="CASCADE"), nullable=False, index=True, unique=True))
    
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    called_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    
    def __repr__(self):
        return f"<Queue Entry uid={self.uid}, Queue uid={self.queue_uid}, Patient uid={self.patient_uid}, Appointment uid={self.appointment_uid}, Status={self.status}>"

    # Relationship
    patient: "Patient" = Relationship(
        back_populates="queue_entries", sa_relationship_kwargs={"lazy": "selectin"})
    appointment: "Appointment" = Relationship(
        back_populates="queue_entries", sa_relationship_kwargs={"lazy": "selectin"})
    queues: "Queue" = Relationship(
        back_populates="queue_entries", sa_relationship_kwargs={"lazy": "selectin"})