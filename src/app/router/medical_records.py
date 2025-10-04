from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from src.app.core import errors
from src.app.core.dependencies import RoleChecker, get_current_user
from src.app.database.main import get_session
from src.app.schemas import MedicalRecordUpdate
from src.app.services import medical_records as med_service
from src.app.models import Admin, AdminType, Doctor, MedicalRecord

med_router = APIRouter(tags=["Medical Records"])
admin_only = Depends(RoleChecker(["admin"]))
doctor_only = Depends(RoleChecker(["doctor"]))
admin_and_doctor = Depends(RoleChecker(["doctor", "admin"]))


@med_router.get("medical_records/{record_id}", status_code=status.HTTP_200_OK, dependencies=[admin_and_doctor])
async def get_medical_record(record_id: str, session: AsyncSession = Depends(get_session), current_user: Admin | Doctor = Depends(get_current_user)):
    
    if current_user.admin_type == AdminType.SUPER_ADMIN:
        raise errors.RoleCheckAccess()
    
    record = await med_service.get_record(record_id=record_id, session=session)

    if current_user.hospital_uid != record.hospital_uid:
        raise errors.NotAuthorized()
    
    if record is None:
        raise errors.MedicalRecordNotFound()
    else:
        return record
    

@med_router.get("hospitals/{hospital_uid}/medical_records", status_code=status.HTTP_200_OK, dependencies=[admin_only], response_model=List[MedicalRecord])
async def get_hospital_medical_records(
    hospital_uid: str,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    patient_uid: Optional[str] = None,
    doctor_uid: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: Admin = Depends(get_current_user)
):
    
    if current_user.admin_type == AdminType.HOSPITAL_ADMIN and current_user.hospital_uid == hospital_uid:
        records = await med_service.get_medical_records_by_hospital(
            session=session,
            hospital_uid=hospital_uid,
            page=page,
            per_page=per_page,
            patient_uid=patient_uid,
            doctor_uid=doctor_uid,
            date_from=date_from,
            date_to=date_to,
        )
    
        return records
    else:
        raise errors.NotAuthorized()
    

@med_router.get('/medical_records/{patient_id}', status_code=status.HTTP_200_OK, dependencies=[admin_only], response_model=List[MedicalRecord])
async def get_patient_records(patient_id: str, hospital_id: str, skip: int = 0, limit: int = 100,  session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    
    if current_user.admin_type == AdminType.SUPER_ADMIN:
        raise errors.RoleCheckAccess()
    
    if current_user.hospital_uid != hospital_id:
        raise errors.NotAuthorized()
    
    patient_records = await med_service.get_patient_records(patient_id=patient_id, hospital_id=hospital_id, skip=skip, limit=limit, session=session)

    return patient_records


med_router.patch('medical_records/{record_id}', status_code=status.HTTP_202_ACCEPTED, dependencies=[admin_and_doctor])
async def update_record(record_id: str, payload: MedicalRecordUpdate, session: AsyncSession = Depends(get_current_user), current_user: Admin | Doctor = Depends(get_current_user)):
    
    if current_user.admin_type == AdminType.SUPER_ADMIN:
        raise errors.RoleCheckAccess()
    
    record = await med_service.get_record(record_id=record_id, session=session)

    if record is None:
        raise errors.MedicalRecordNotFound()
    
    if current_user.hospital_uid != record.hospital_uid:
        raise errors.NotAuthorized()
    
    updated_record = await med_service.update_medical_record(record_id=record_id, session=session)

    return updated_record

    

