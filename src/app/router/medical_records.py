import uuid
from src.app.core import permissions
from src.app.schemas import MedicalRecordCreate
from src.app.models import (
    MedicalRecord,
    User,
)
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.app.core.dependencies import get_current_user
from src.app.database.main import get_session
from src.app.schemas import MedicalRecordUpdate, MedicalRecordRead
from src.app.services import medical_records as med_service, appointment as apt_service
from src.app.core import errors as exec_errors

med_router = APIRouter(tags=["Medical Records"])


@med_router.post('/medical_records', status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    appointment_id: uuid.UUID,
    payload: MedicalRecordCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Practitioners or hospital admins create medical records through appointment routes.
    Practitioner ID, patient ID, and hospital ID are assigned automatically from the appointment.
    """ 
    
    # Fetch appointment details
    appointment = await apt_service.get_appointment_by_id(appointment_uid=appointment_id, session=session)
    if appointment is None:
        raise exec_errors.AppointmentNotFound()

    # Role check - only practitioners and hospital admins can create medical records
    permissions.can_access_medical_record_role(current_user, appointment.hospital_uid)

    # Populate IDs from appointment and create
    payload.hospital_uid = appointment.hospital_uid
    payload.patient_uid = appointment.patient_uid
    payload.practitioner_uid = appointment.practitioner_uid

    new_record = await med_service.create_medical_record(payload=payload, session=session)
    return new_record



@med_router.get("/medical_records/hospital-medical-records", status_code=status.HTTP_200_OK, response_model=List[MedicalRecord])
async def get_hospital_medical_records(hospital_id: uuid.UUID, offset: int = 0, limit: int = 10, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    # Role check only hospital admin and department admin can access
    permissions.get_hospital_medical_record_access(current_user, hospital_id)

    records = await med_service.get_all_hospital_medical_records(hospital_id=hospital_id, offset=offset, limit=limit, session=session)

    return records


@med_router.get("/medical_records/record", status_code=status.HTTP_200_OK, response_model=MedicalRecord)
async def get_medical_record(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    
    record = await med_service.get_medical_record_by_id(record_id, session)

    if not record:
        raise exec_errors.MedicalRecordNotFound()
    
    permissions.can_access_medical_records(current_user, record.hospital_uid)
    
    return record


# Get patient medical records
@med_router.get("/medical_records/patient-records", status_code=status.HTTP_200_OK, response_model=List[MedicalRecordRead])
async def get_patient_medical_records(
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID,
    offset: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Role check - only hospital admins, department admins, practitioner and patients can access
    permissions.can_access_patient_medical_records(current_user, patient_id, hospital_id)
    
    records = await med_service.get_medical_record_by_patient(patient_id, hospital_id, offset, limit, session)

    return records


@med_router.put("/medical_records/update-record", status_code=status.HTTP_200_OK, response_model=MedicalRecord)
async def update_medical_record_endpoint(
    record_id: uuid.UUID,
    payload: MedicalRecordUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    
    # Fetch existing record
    existing_record = await med_service.get_medical_record_by_id(record_id, session)
    if existing_record is None:
        raise exec_errors.MedicalRecordNotFound()

    
    # Check if the user can update this medical record
    permissions.can_update_medical_record(current_user, existing_record.hospital_uid)

    updated_record = await med_service.update_patient_medical_record(record_id, payload, session)
    return updated_record


@med_router.get("/medical_records/search/{hospital_id}", status_code=status.HTTP_200_OK, response_model=List[MedicalRecord])
async def search_medical_records_endpoint(
        hospital_uid: uuid.UUID,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        patient_uid: Optional[uuid.UUID] = Query(None),
        practitioner_uid: Optional[uuid.UUID] = Query(None),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ):

    # Role check - only practitioners and hospital admins can search medical records
    permissions.can_access_medical_record_role(current_user, hospital_uid)

    records = await med_service.search_medical_records_by_hospital(
            session=session,
            hospital_uid=hospital_uid,
            page=page,
            per_page=per_page,
            patient_uid=patient_uid,
            practitioner_uid=practitioner_uid,
            date_from=date_from,
            date_to=date_to,
        )

    return records

