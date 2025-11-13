import sqlalchemy.dialects.postgresql as pg
import uuid
from sqlmodel import SQLModel, Field, Relationship, ForeignKey, Column
from sqlalchemy import Integer, String, DateTime, Enum as pgEnum, Text
from datetime import datetime, timezone, date
from enum import Enum
from typing import Optional, List


class UserRoles(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
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


class ViewAppointmentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"
    IN_PROGRESS = "in_progress"
    RESCHEDULED = "rescheduled"
    ALL = "all"


class DoctorStatus(str, Enum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class HospitalStatus(str, Enum):
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"

# Enum for Hospital Ownership type


class HospitalType(str, Enum):
    PRIVATE = "private"
    GOVERNMENT = "government"
    NGO = "ngo"


class RecordType(str, Enum):
    DIAGNOSIS = "diagnosis"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    NOTE = "note"


class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    username: str = Field(sa_column=Column(
        String, nullable=False, unique=True))
    email: str = Field(sa_column=Column(
        String, unique=True, nullable=False, index=True))
    hashed_password: str = Field(exclude=True)
    role: UserRoles = Field(sa_column=Column(
        pgEnum(UserRoles, name="user_role", create_type=True), nullable=False))
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
    hospital: Optional["Hospital"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    admin: Optional["Admin"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    patient: Optional["Patient"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    doctor: Optional["Doctor"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    notifications: List["Notification"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

# Hospital Model


class Hospital(SQLModel, table=True):
    __tablename__ = "hospitals"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    hospital_name: str = Field(default=None, sa_column=Column(
        String, unique=True, nullable=False))
    full_address: str = Field(default=None)
    state: str = Field(default=None)
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    website: Optional[str] = Field(default=None)
    license_number: str = Field(default=None, sa_column=Column(
        String, unique=True, nullable=False))
    phone_number: str = Field(default=None)
    registration_number: str = Field(
        default=None, sa_column=Column(String, unique=True, nullable=False))
    ownership_type: HospitalType = Field(default=HospitalType.PRIVATE, sa_column=Column(
        pgEnum(HospitalType, name="hospital_type", create_type=True), nullable=False))
    status: HospitalStatus = Field(default=HospitalStatus.UNDER_REVIEW, sa_column=Column(
        pgEnum(HospitalStatus, name="hospital_status", create_type=True), nullable=False))
    hospital_ceo: str = Field(default=None)
    is_verified: bool = Field(
        default=False, sa_column=Column(pg.BOOLEAN, nullable=False))

    def __repr__(self):
        return f"<Hospital uid={self.uid}, hospital_name={self.hospital_name}>"

    # Relationship
    user: "User" = Relationship(
        back_populates="hospital", sa_relationship_kwargs={"lazy": "selectin"})
    doctor: List["Doctor"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                          "lazy": "selectin"}, passive_deletes=True)
    admin: List["Admin"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                        "lazy": "selectin"}, passive_deletes=True)
    appointment: List["Appointment"] = Relationship(
        back_populates="hospital", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    department: List["Department"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                                  "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    medical_record: List["MedicalRecord"] = Relationship(back_populates="hospital", sa_relationship_kwargs={
                                                         "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)


# Patient Model
class Patient(SQLModel, table=True):
    __tablename__ = "patients"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    full_name: str = Field(default=None)
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
        return f"<Patient uid= {self.uid}, Patient's Full_name= {self.full_name}>"

    # Relationship
    user: "User" = Relationship(
        back_populates="patient", sa_relationship_kwargs={"lazy": "selectin"})
    appointment: List["Appointment"] = Relationship(
        back_populates="patient", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    medical_record: List["MedicalRecord"] = Relationship(back_populates="patient", sa_relationship_kwargs={
                                                         "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)


# Doctor Model
class Doctor(SQLModel, table=True):
    __tablename__ = "doctors"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    full_name: str = Field(default=None)
    phone_number: str = Field(default=None)
    date_of_birth: Optional[date] = Field(default=None)
    gender: str = Field(default=None)
    country: str = Field(default=None)
    state_of_residence: str = Field(default=None)
    home_address: str = Field(default=None)
    hospital_uid: Optional[uuid.UUID] = Field(default=None, sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("hospitals.uid", ondelete="CASCADE"), nullable=True, index=True))
    department_uid: Optional[uuid.UUID] = Field(default=None, sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("departments.uid", ondelete="CASCADE"), nullable=True, index=True))
    license_number: str = Field(default=None, sa_column=Column(
        String, unique=True, nullable=False))
    specialization: str = Field(default=None)
    qualification: str = Field(default=None)
    bio: Optional[str] = Field(default=None)
    status: DoctorStatus = Field(default=DoctorStatus.UNDER_REVIEW, sa_column=Column(
        pgEnum(DoctorStatus, name="doctor_status", create_type=True), nullable=False))
    is_available: bool = Field(
        default=True, sa_column=Column(pg.BOOLEAN, nullable=False))
    years_of_experience: int = Field(default=None)
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))

    def __repr__(self):
        return f"<Doctor uid={self.uid}, Doctor full_name={self.full_name}>"

    # Relationship
    user: "User" = Relationship(
        back_populates="doctor", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="doctor", sa_relationship_kwargs={"lazy": "selectin"})
    appointment: List["Appointment"] = Relationship(
        back_populates="doctor", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)
    department: "Department" = Relationship(
        back_populates="doctors", sa_relationship_kwargs={"lazy": "selectin"})
    medical_record: List["MedicalRecord"] = Relationship(
        back_populates="doctor", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True)


# Admin Model
class Admin(SQLModel, table=True):
    __tablename__ = "admins"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), nullable=False, primary_key=True))
    full_name: str = Field(default=None)
    hospital_uid: Optional[uuid.UUID] = Field(sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("hospitals.uid", ondelete="CASCADE"), nullable=True, index=True))
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    admin_type: AdminType = Field(sa_column=Column(
        pg.ENUM(AdminType, name="admin_type", create_type=True), nullable=False))
    department_uid: Optional[uuid.UUID] = Field(sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("departments.uid", ondelete="CASCADE"), nullable=True, index=True))
    notes: Optional[str] = None

    def __repr__(self):
        return f"<ADMIN: uid={self.uid}, Name={self.full_name}, Admin Type={self.admin_type}>"

    # Relationships
    user: "User" = Relationship(
        back_populates="admin", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="admin", sa_relationship_kwargs={"lazy": "selectin"})
    department: Optional["Department"] = Relationship(
        back_populates="admin", sa_relationship_kwargs={"lazy": "selectin"})

# Appointment model


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"

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
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING, sa_column=Column(
        pgEnum(AppointmentStatus, name="appointment_status", create_type=True), nullable=False))
    doctor_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "doctors.uid", ondelete="CASCADE"), nullable=True, index=True))
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
        return f"<Appointment uid={self.uid}, Patient uid={self.patient_uid}, Doctor uid={self.doctor_uid}, Status={self.status}>"

    # Relationship
    patient: "Patient" = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"})
    doctor: "Doctor" = Relationship(
        back_populates="appointment", sa_relationship_kwargs={"lazy": "selectin"})
    department: "Department" = Relationship(
        back_populates="appointments", sa_relationship_kwargs={"lazy": "selectin"})
    reschedule_history: List["RescheduleHistory"] = Relationship(
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
    __tablename__ = "departments"

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
    doctors: List["Doctor"] = Relationship(
        back_populates="department", sa_relationship_kwargs={"lazy": "selectin"})
    appointments: List["Appointment"] = Relationship(
        back_populates="department", sa_relationship_kwargs={"lazy": "selectin"})

# Medical Record Model


class MedicalRecord(SQLModel, table=True):
    __tablename__ = "medical_records"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    patient_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "patients.uid", ondelete="CASCADE"), nullable=False, index=True))
    doctor_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "doctors.uid", ondelete="CASCADE"), nullable=False, index=True))
    hospital_uid: Optional[uuid.UUID] = Field(sa_column=Column(pg.UUID(
        as_uuid=True), ForeignKey("hospitals.uid", ondelete="CASCADE"), nullable=True, index=True))
    record_type: RecordType = Field(default=RecordType.PRESCRIPTION, sa_column=Column(
        pg.ENUM(RecordType, name="record_type", create_type=True), nullable=True))
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
        return f"<Medical Record uid={self.uid}, Patient uid={self.patient_uid}, Doctor uid={self.doctor_uid}, Hospital uid={self.hospital_uid}, Record Type={self.record_type}>"

    # Relationships
    files: List["MedicalRecordFile"] = Relationship(back_populates="medical_record", sa_relationship_kwargs={
                                                    "lazy": "selectin", "cascade": "all, delete-orphan"}, passive_deletes=True)
    patient: "Patient" = Relationship(
        back_populates="medical_record", sa_relationship_kwargs={"lazy": "selectin"})
    doctor: "Doctor" = Relationship(
        back_populates="medical_record", sa_relationship_kwargs={"lazy": "selectin"})
    hospital: "Hospital" = Relationship(
        back_populates="medical_record", sa_relationship_kwargs={"lazy": "selectin"})


class MedicalRecordFile(SQLModel, table=True):
    __tablename__ = "medical_record_files"

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


# Signup Link - Table to store generated tokens for admins/doctors signup links.
class SignupLink(SQLModel, table=True):
    __tablename__ = "signup_links"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    token: str = Field(sa_column=Column(String, unique=True, index=True))
    email: str = Field(sa_column=Column(String, nullable=False))
    hospital_uid: str = Field(sa_column=Column(String, nullable=False))
    department_uid: str = Field(sa_column=Column(String, nullable=True))
    admin_type: AdminType = Field(sa_column=Column(
        pg.ENUM(AdminType, name="admin_type", create_type=True), nullable=False))
    notes: Optional[str] = None
    is_used: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )

    def __repr__(self):
        return f"<SignupLink: uid={self.uid}, email= {self.email}, is_used={self.is_used}>"


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

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
    __tablename__ = "messages"

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
    __tablename__ = "blacklistedtokens"

    id: int = Field(sa_column=Column(
        Integer, primary_key=True, nullable=False))
    token_jti: str = Field(sa_column=Column(String, unique=True))
    session_id: str = Field(sa_column=Column(String, index=True, unique=True))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refreshtokens"

    uid: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, sa_column=Column(
        pg.UUID(as_uuid=True), primary_key=True, index=True))
    jti: str = Field(sa_column=Column(String, index=True, unique=True))
    user_uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey(
        "users.uid", ondelete="CASCADE"), nullable=False, index=True))
    session_id: str = Field(sa_column=Column(String, index=True, unique=True))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    )
    revoked: bool = Field(default=False)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

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


