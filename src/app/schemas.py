from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
import uuid
from datetime import datetime, date
from typing import Optional, List
from src.app.models import UserRoles, HospitalType, AdminType, AppointmentStatus, RecordType, DoctorStatus, HospitalStatus


class EmailStrLower(EmailStr):
    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls.to_lower

    @classmethod
    def to_lower(cls, v):
        return v.lower().strip() if isinstance(v, str) else v
    
###############......User Auth Model........############
class UserBase(BaseModel):
    username: str
    email: EmailStrLower
    role: UserRoles = UserRoles.PATIENT

###########.........User Registration.........#########
class RegisterUser(UserBase):
    password: str

    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        if not any(char.islower() for char in value):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isupper() for char in value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char in "!@#$%^&*()_+[]{}|;:,.<>?/~" for char in value):
            raise ValueError('Password must contain at least one special character')
        return value


class RegisterAdminUser(BaseModel):
    username: str
    email: EmailStrLower
    role: UserRoles.ADMIN
    password: str

    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        if not any(char.islower() for char in value):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isupper() for char in value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char in "!@#$%^&*()_+[]{}|;:,.<>?/~" for char in value):
            raise ValueError('Password must contain at least one special character')
        return value


class UserRead(UserBase):
    uid: uuid.UUID
    role: UserRoles
    is_active: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


#################...........Hospital Model.............#########
class HospitalBase(BaseModel):
    hospital_name: str
    full_address: str
    state: str
    website: Optional[str] = None
    license_number: str
    phone_number: str
    registration_number: str
    ownership_type: HospitalType = HospitalType.PRIVATE
    hospital_ceo: str

class HospitalProfileCreate(HospitalBase):
    pass

class HospitalProfileUpdate(BaseModel):
    hospital_name: Optional[str] = None
    full_address: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    registration_number: Optional[str] = None
    ownership_type: Optional[HospitalType] = None
    hospital_ceo: Optional[str] = None

class VerifyHospital(BaseModel):
    status: HospitalStatus

class HospitalRead(HospitalBase):
    uid: uuid.UUID
    user_uid: uuid.UUID
    is_verified: bool = False
    status: HospitalStatus = HospitalStatus.UNDER_REVIEW

    model_config = ConfigDict(from_attributes=True)


##########........Patient Model........##########
class PatientBase(BaseModel):
    full_name: str
    hospital_card_id: str
    phone_number: str
    date_of_birth: date
    gender: str
    country: str
    state_of_residence: str
    home_address: str
    blood_type: str
    emergency_contact_full_name: str
    emergency_contact_phone_number: str

class PatientProfileCreate(PatientBase):
    pass

class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    hospital_card_id: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    state_of_residence: Optional[str] = None
    home_address: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact_full_name: Optional[str] = None
    emergency_contact_phone_number: Optional[str] = None

class PatientRead(PatientBase):
    uid: uuid.UUID
    user_uid: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


##########.........Doctor Model...........################
class DoctorBase(BaseModel):
    full_name: str
    phone_number: str 
    date_of_birth: Optional[date] = None
    gender: str
    country: str
    state_of_residence: str
    home_address: str
    hospital_uid: Optional[uuid.UUID] = None
    department_uid: Optional[uuid.UUID] = None
    license_number: str
    specialization: str
    qualification: str
    bio: Optional[str] = None
    is_available: bool = True

class DoctorProfileCreate(DoctorBase):
    pass

class DoctorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None 
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    state_of_residence: Optional[str] = None
    hospital_uid: Optional[uuid.UUID] = None
    department_uid: Optional[uuid.UUID] = None
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    bio: Optional[str] = None
    is_available: Optional[bool] = None
    years_of_experience: Optional[int] = None
    consultation_fee: Optional[float] = None

class DoctorAssign(BaseModel):
    doctor_uid: str

class DoctorRead(DoctorBase):
    uid: uuid.UUID 
    status: DoctorStatus = DoctorStatus.UNDER_REVIEW
    user_uid: uuid.UUID
    department_uid: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



#########........Admin Model...........#########
class AdminBase(BaseModel):
    full_name: str
    hospital_uid: Optional[uuid.UUID] = None
    admin_type: AdminType = AdminType.HOSPITAL_ADMIN
    department_uid: Optional[uuid.UUID] = None

class AdminProfileCreate(AdminBase):
    pass

class AdminProfileUpdate(BaseModel):
    admin_type: Optional[AdminType] = None
    notes: Optional[str] = None
    department_uid: Optional[uuid.UUID] = None

class AssignAdminDuty(BaseModel):
    notes: str

class AdminRead(AdminBase):
    uid: uuid.UUID
    user_uid: uuid.UUID
    created_at: datetime
    updated_at: datetime
    notes: str

    model_config = ConfigDict(from_attributes=True)


#########.........Appointment Model..........#########
class AppointmentBase(BaseModel):
    appointment_note: str
    scheduled_time: datetime
    hospital_uid: uuid.UUID
    department_uid: uuid.UUID

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentCancel(BaseModel):
    cancellation_reason: str

"""Might be needed in future"""
# class AppointmentUpdate(BaseModel):
#     appointment_note: Optional[str] = None
#     scheduled_time: Optional[datetime] = None
#     rescheduled_from: Optional[uuid.UUID] = None
#     hospital_uid: Optional[uuid.UUID] = None
#     department_uid: Optional[uuid.UUID] = None

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus

class RescheduleAppointment(BaseModel):
    new_time: datetime
    reason: str

class AppointmentRead(AppointmentBase):
    uid: uuid.UUID
    patient_uid: uuid.UUID
    doctor_uid: uuid.UUID
    status: AppointmentStatus = AppointmentStatus.PENDING
    rescheduled_from: Optional[datetime] = None
    check_in_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


#########............Department Model.............###########
class DepartmentCreate(BaseModel):
    name: str

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None

class DepartmentRead(BaseModel):
    uid: uuid.UUID
    name: str
    hospital_uid: uuid.UUID
    appointment_uid: uuid.UUID
    doctor_iud: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



#########............Medical Record Model.........############
class MedicalRecordCreate(BaseModel):
    patient_uid: Optional[uuid.UUID] = None
    doctor_uid: Optional[uuid.UUID] = None
    hospital_uid: Optional[uuid.UUID] = None
    record_type: RecordType = RecordType.PRESCRIPTION
    description: str
    record_date: datetime

class MedicalRecordUpdate(BaseModel):
    record_type: Optional[RecordType] = None
    description: Optional[str] = None
    record_date: Optional[datetime] = None


class MedicalRecordRead(BaseModel):
    uid: uuid.UUID
    patient_uid: uuid.UUID
    doctor_uid: uuid.UUID
    hospital_uid: Optional[uuid.UUID] = None
    record_type: RecordType
    description: str
    record_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



########..........Message Model.........#########

class MessageCreate(BaseModel):
    receiver_uid: uuid.UUID
    content: str

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageMarkAsRead(BaseModel):
    is_read: bool = True

class MessageRead(BaseModel):
    uid: uuid.UUID
    sender_uid: uuid.UUID
    receiver_uid: uuid.UUID
    content: str
    timestamp: datetime
    is_read: bool = False

    model_config = ConfigDict(from_attributes=True)


class LoginData(BaseModel):
    username: str
    password: str

    @field_validator("username")
    def normalize_username_or_email(cls, v: str) -> str:
        # If it looks like an email, lowercase it
        if "@" in v:
            return v.lower()
        return v

class EmailModel(BaseModel):
    mail_to: List[str]


class PasswordResetRequest(BaseModel):
    email_address: EmailStr

class ConfirmPasswordReset(BaseModel):
    new_password: str
    confirm_password: str


#############.....USER RETURN TO GET UUID CREATE FOR THE EXTRA TABLES FOR DEVELOPMENT PURPOSE
class UserReadMe(UserBase):
    uid: uuid.UUID
    role: UserRoles
    is_active: bool = False
    created_at: datetime
    updated_at: datetime
    admin: Optional[AdminRead]
    patient: Optional[PatientRead]
    doctor: Optional[DoctorRead]
    hospital: Optional[HospitalRead]

    model_config = ConfigDict(from_attributes=True)


class DataPlusMessage(BaseModel):
    message: str
    data: MessageRead