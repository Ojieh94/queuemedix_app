from src.app.core import permissions
from email import errors
from src.app.schemas import MedicalRecordCreate
from src.app.models import (
    MedicalRecord,
    AdminType,
    User,
    UserRoles
)
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from src.app.core.dependencies import get_current_user
from src.app.database.main import get_session
from src.app.schemas import MedicalRecordUpdate
from src.app.services import medical_records as med_service, appointment as apt_service
from src.app.core import errors

med_router = APIRouter(tags=["Medical Records"])


@med_router.post('/medical_records/{appointment_id}', status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    appointment_id: str,
    payload: MedicalRecordCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Doctors or hospital admins create medical records through appointment routes.
    Doctor ID, patient ID, and hospital ID are assigned automatically from the appointment.
    """

    # Role check - only doctors and hospital admins can create medical records
    permissions.can_access_medical_record_role(current_user)

    # Fetch appointment details
    appointment = await apt_service.get_appointment_by_id(appointment_uid=appointment_id, session=session)
    if appointment is None:
        raise errors.AppointmentNotFound()

    # Check if the user can create a medical record for this appointment
    permissions.can_create_medical_record_for_appointment(current_user, appointment)

    # Populate IDs from appointment and create
    payload.hospital_uid = appointment.hospital_uid
    payload.patient_uid = appointment.patient_uid
    payload.doctor_uid = appointment.doctor_uid

    new_record = await med_service.create_medical_record(payload=payload, session=session)
    return new_record



@med_router.get("/medical_records/{hospital_id}", status_code=status.HTTP_200_OK, response_model=List[MedicalRecord])
async def get_hospital_medical_records(hospital_id: str, offset: int = 0, limit: int = 10, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    # Role check only hospital admin and department admin can access
    permissions.get_hospital_medical_record_access(current_user, hospital_id)

    records = await med_service.get_all_hospital_medical_records(hospital_id=hospital_id, offset=offset, limit=limit, session=session)

    return records


@med_router.get("/medical_records/{record_id}", status_code=status.HTTP_200_OK, response_model=MedicalRecord)
async def get_medical_record(
    record_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    permissions.can_access_medical_records(current_user)
    
    record = await med_service.get_medical_record_by_id(record_id, session)

    if record is None:
        raise errors.MedicalRecordNotFound()
    
    elif record.hospital_uid != current_user.admin.hospital_uid:
        raise errors.NotAuthorized()
    
    return record


# Get patient medical records
@med_router.get("/medical_records/{patient_id}", status_code=status.HTTP_200_OK, response_model=MedicalRecord)
async def get_patient_medical_records(
    patient_id: str,
    hospital_id: str,
    offset: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Role check - only hospital admins, department admins, doctors and patients can access
    permissions.can_access_patient_medical_records(current_user, patient_id, hospital_id)
    
    record = await med_service.get_medical_record_by_patient(patient_id, hospital_id, offset, limit, session)

    return record


@med_router.put("/medical_records/{record_id}", status_code=status.HTTP_200_OK, response_model=MedicalRecord)
async def update_medical_record_endpoint(
    record_id: str,
    payload: MedicalRecordUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Role check - only doctors and hospital admins can update medical records
    permissions.can_access_medical_record_role(current_user)

    # Fetch existing record
    existing_record = await med_service.get_medical_record_by_id(record_id, session)
    if existing_record is None:
        raise errors.MedicalRecordNotFound()

    # Check if the user can update this medical record
    permissions.can_update_medical_record(current_user, existing_record)

    updated_record = await med_service.update_patient_medical_record(record_id, payload, session)
    return updated_record


@med_router.get("/medical_records/search/{hospital_id}", status_code=status.HTTP_200_OK, response_model=List[MedicalRecord])
async def search_medical_records_endpoint(
        hospital_id: str,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        patient_uid: Optional[str] = Query(None),
        doctor_uid: Optional[str] = Query(None),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ):
    # Role checks similar to get_hospital_medical_records
    if current_user.role == UserRoles.ADMIN and current_user.admin.admin_type == AdminType.SUPER_ADMIN:
        raise errors.RoleCheckAccess()

    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.hospital_uid != hospital_id:
                raise errors.NotAuthorized()

    records = await med_service.search_medical_records_by_hospital(
            session=session,
            hospital_uid=hospital_id,
            page=page,
            per_page=per_page,
            patient_uid=patient_uid,
            doctor_uid=doctor_uid,
            date_from=date_from,
            date_to=date_to,
        )

    return records

