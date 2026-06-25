from pydantic import AfterValidator, BaseModel, EmailStr, field_validator, ConfigDict
import uuid
from datetime import datetime, date
from typing import Annotated, Optional
from src.app.models import AdminTypeUpdate, UserRoles, HospitalType, AdminType, AppointmentStatus, RecordType, PractitionerStatus, HospitalStatus, PractitionerType
from src.app import validators

######### ............Department Model.............###########
class DepartmentCreate(BaseModel):
    name: str


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None

class DepartmentRead(BaseModel):
    uid: uuid.UUID
    name: str
   

    model_config = ConfigDict(from_attributes=True)


class DepartmentResponse(BaseModel):
    uid: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


def lower_email(value: EmailStr) -> str:
    return value.lower()

EmailStrLower = Annotated[
    EmailStr,
    AfterValidator(lower_email)
]

############### ......User Auth Model........############


class UserBase(BaseModel):
    email: EmailStrLower
    role: UserRoles = UserRoles.PATIENT

########### .........User Registration.........#########


class RegisterUser(UserBase):
    password: str

    @field_validator('password')
    def validate_password(cls, value: str) -> str:
        return validators.validate_password_strength(value)
    

class RegisterPractitionerUser(BaseModel):
    email: EmailStrLower
    role: UserRoles = UserRoles.PRACTITIONER
    password: str

    @field_validator('password')
    def validate_password(cls, value: str) -> str:
        return validators.validate_password_strength(value)


class RegisterAdminUser(BaseModel):
    email: EmailStrLower
    role: UserRoles = UserRoles.ADMIN
    password: str

    @field_validator('password')
    def validate_password(cls, value: str) -> str:
        return validators.validate_password_strength(value)



class UserRead(UserBase):
    uid: uuid.UUID
    username: str
    is_active: bool = False
    profile_picture: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserProfile(BaseModel):
    uid: uuid.UUID
    profile_picture: Optional[str] = None



################# ...........Hospital Model.............#########
class HospitalBase(BaseModel):
    hospital_name: str
    full_address: str
    state: str
    website: Optional[str] = None
    license_number: str
    phone_number: str
    cover_image: str
    registration_number: str
    ownership_type: HospitalType = HospitalType.PRIVATE
    hospital_ceo: str
    about: Optional[str] = None


class HospitalProfileCreate(HospitalBase):
    pass


class HospitalProfileUpdate(BaseModel):
    hospital_name: Optional[str] = None
    full_address: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    about: Optional[str] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    registration_number: Optional[str] = None
    ownership_type: Optional[HospitalType] = None
    cover_image: Optional[str] = None
    hospital_ceo: Optional[str] = None

    @field_validator('hospital_name', 'full_address', 'about', 'state', 'license_number', 'phone_number', 'registration_number', 'hospital_ceo', 'cover_image')
    def validate_non_empty_strings(cls, value):
        if value is None:
            return value
        if not value or not value.strip():
            raise ValueError(
                'This field cannot be empty or contain only whitespace')
        return value.strip()


class VerifyHospital(BaseModel):
    status: HospitalStatus


class HospitalRatingCreate(BaseModel):
    rating: float

    @field_validator('rating')
    def validate_rating(cls, value):
        if value < 1 or value > 5:
            raise ValueError('Rating must be between 1 and 5')

        decimal_rating = Decimal(str(value))  #type: ignore  # noqa: F821
        if decimal_rating.as_tuple().exponent < -1:
            raise ValueError('Rating can have at most one decimal place')

        return float(decimal_rating.quantize(Decimal('0.1'))) #type: ignore  # noqa: F821


class HospitalRead(HospitalBase):
    uid: uuid.UUID
    is_verified: bool = False
    status: HospitalStatus = HospitalStatus.UNDER_REVIEW
    average_rating: float = 0.0
    cover_image: str

    model_config = ConfigDict(from_attributes=True)


class HospitalAppointmentStats(BaseModel):
    total_appointments: int
    todays_appointments: int
    pending_appointments: int
    completed_appointments: int
    canceled_appointments: int
    in_progress_appointments: int

    model_config = ConfigDict(from_attributes=True)

class HospitalResponse(BaseModel):
    uid: uuid.UUID
    hospital_name: str
    full_address: str
    user: UserProfile | None

    model_config = ConfigDict(from_attributes=True)


########## ........Patient Model........##########
class PatientBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
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
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
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
    user: UserProfile | None

    model_config = ConfigDict(from_attributes=True)


########## .........Practitioner Model...........################
class PractitionerBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    phone_number: str
    date_of_birth: Optional[date] = None
    gender: str
    country: str
    state_of_residence: str
    home_address: str
    hospital_uid: Optional[uuid.UUID] = None
    department_uid: Optional[uuid.UUID] = None
    license_number: str
    years_of_experience: Optional[int] = None
    specialization: str
    qualification: str
    bio: Optional[str] = None
    is_available: bool = True
    practitioner_type: PractitionerType


class PractitionerProfileCreate(PractitionerBase):
    pass


class PractitionerProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
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


class PractitionerAssign(BaseModel):
    practitioner_uid: uuid.UUID


class PractitionerRead(PractitionerBase):
    uid: uuid.UUID
    status: PractitionerStatus = PractitionerStatus.UNDER_REVIEW
    hospital: HospitalResponse | None
    department: DepartmentResponse | None
    user: UserProfile | None
    practitioner_type: PractitionerType

    model_config = ConfigDict(from_attributes=True)

class PractitionerResponse(BaseModel):
    uid: uuid.UUID
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    specialization: str
    bio: Optional[str] = None
    is_available: bool = True
    user: UserProfile | None
    department: DepartmentResponse | None
    practitioner_type: PractitionerType

    model_config = ConfigDict(from_attributes=True)



######### ........Admin Model...........#########
class AdminBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    hospital_uid: Optional[uuid.UUID] = None
    admin_type: AdminType = AdminType.HOSPITAL_ADMIN
    department_uid: Optional[uuid.UUID] = None


class AdminProfileCreate(AdminBase):
    pass


class AdminProfileUpdate(AdminBase):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    admin_type: Optional[AdminTypeUpdate] = None
    notes: Optional[str] = None
    department_uid: Optional[uuid.UUID] = None


class AssignAdminDuty(BaseModel):
    notes: str


class AdminRead(AdminBase):
    uid: uuid.UUID
    hospital: HospitalResponse | None
    department: DepartmentResponse | None
    notes: Optional[str] = None
    user: UserProfile | None

    model_config = ConfigDict(from_attributes=True)


######### .........Appointment Model..........#########
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
    patient: PatientRead | None
    practitioner: PractitionerResponse | None
    hospital: HospitalResponse | None
    department: DepartmentResponse | None
    status: AppointmentStatus = AppointmentStatus.PENDING
    rescheduled_from: Optional[datetime] = None
    check_in_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)




######## ............Medical Record Model.........############
class MedicalRecordCreate(BaseModel):
    patient_uid: Optional[uuid.UUID] = None
    practitioner_uid: Optional[uuid.UUID] = None
    hospital_uid: Optional[uuid.UUID] = None
    record_type: RecordType = RecordType.PRESCRIPTION
    description: str
    record_date: datetime


class MedicalRecordUpdate(BaseModel):
    record_type: Optional[RecordType] = None
    description: Optional[str] = None
    record_date: Optional[datetime] = None


class MedicalRecordFile(BaseModel):
    uid: uuid.UUID
    record_uid: uuid.UUID
    file_name: str
    file_url: str  # S3/GCP/local storage path
    file_type: str  # e.g. pdf, jpg, png, docx
    uploaded_at: datetime 

    model_config = ConfigDict(from_attributes=True)


class MedicalRecordRead(BaseModel):
    uid: uuid.UUID
    patient: PatientRead
    practitioner: PractitionerResponse
    hospital: HospitalResponse | None
    record_type: RecordType
    description: str
    files: list[MedicalRecordFile] | None = None
    record_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


######## ..........Message Model.........#########

class MessageCreate(BaseModel):
    receiver_uid: uuid.UUID
    content: str


class MessageUpdate(BaseModel):
    content: Optional[str] = None


class MessageMarkAsRead(BaseModel):
    is_read: bool = True


class MessageRead(BaseModel):
    uid: uuid.UUID
    sender: UserRead
    receiver: UserRead
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
    mail_to: str


class PasswordResetRequest(BaseModel):
    email_address: EmailStr


class ConfirmPasswordReset(BaseModel):
    new_password: str
    confirm_password: str


# .....USER RETURN TO GET UUID CREATE FOR THE EXTRA TABLES FOR DEVELOPMENT PURPOSE
class UserReadMe(UserBase):
    uid: uuid.UUID
    username: str
    is_active: bool = False
    profile_picture: Optional[str]
    created_at: datetime
    updated_at: datetime
    admin: Optional[AdminRead]
    patient: Optional[PatientRead]
    practitioner: Optional[PractitionerRead]
    hospital: Optional[HospitalRead]

    model_config = ConfigDict(from_attributes=True)


class DataPlusMessage(BaseModel):
    message: str
    data: MessageRead

class AppointmentResponse(BaseModel):
    uid: uuid.UUID
    appointment_note: str
    scheduled_time: datetime
    status: AppointmentStatus = AppointmentStatus.PENDING
    check_in_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    practitioner: PractitionerResponse | None
    patient: PatientRead | None
    hospital: HospitalResponse
    rescheduled_from: Optional[datetime] = None
    department: DepartmentResponse | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)