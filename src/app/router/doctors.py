from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import Session
from src.app.models import Admin, AdminType, Doctor, DoctorStatus, UserRoles
from src.app.core.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.app.schemas import DoctorProfileUpdate
from src.app.services import doctors as doctor_service
from src.app.database.main import get_session
from src.app.core import errors

doctor_router = APIRouter(prefix="/doctors", tags=["doctors"])
access_token_bearer = AccessTokenBearer()
admin_only = Depends(RoleChecker(["admin"]))
doctor_only = Depends(RoleChecker(["doctor"]))
admin_and_doctor = Depends(RoleChecker(["doctor", "admin"]))


@doctor_router.get("/search", dependencies=[admin_only], status_code=status.HTTP_200_OK)
async def search_doctors(
    q: str = Query(None, description="Search text (name, specialty, bio)"),
    specialty: str = None,
    hospital_id: int = None,
    is_available: bool = None,
    status: str = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    sort_by: str = "last_name",
    sort_dir: str = "asc",
    session: AsyncSession = Depends(get_session),
    current_user: Admin = Depends(get_current_user),
):
    """Protected endpoint for admins to search doctors"""

    # Super admin → unrestricted
    if current_user.admin_type == AdminType.SUPER_ADMIN:
        result = await doctor_service.search_doctors(
            session=session,
            q=q,
            specialty=specialty,
            hospital_id=hospital_id,
            is_available=is_available,
            status=status,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    # Regular admin → restricted to own hospital
    else:
        if hospital_id and current_user.hospital_uid != hospital_id:
            raise errors.NotAuthorized()

        result = await doctor_service.search_doctors(
            session=session,
            q=q,
            specialty=specialty,
            hospital_id=current_user.hospital_uid,  # enforce hospital scope
            is_available=is_available,
            status=status,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    return result


@doctor_router.get('/', response_model=List[Doctor], status_code=status.HTTP_200_OK, dependencies=[admin_only])
async def get_all_doctors(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: Admin = Depends(get_current_user)):

    """Protected endpoint for super admins to get all doctors"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    doctors = await doctor_service.get_all_doctors(skip=skip, limit=limit, session=session)

    return doctors


@doctor_router.get('/{doctor_id}', status_code=status.HTTP_200_OK, dependencies=[doctor_only])
async def get_doctor(doctor_id: str, session: AsyncSession = Depends(get_session), current_user: Doctor = Depends(get_current_user)):
    
    """Protected endpoint to get a doctor by uuid"""

    if current_user.uid != doctor_id:

        raise errors.NotAuthorized()

    doctor = await doctor_service.get_doctor(doctor_id=doctor_id, session=session)

    if doctor:
        return doctor
    else:
        raise errors.DoctorNotFound
    

@doctor_router.get("/{hospital_id}", status_code=status.HTTP_200_OK, dependencies=[admin_only])
async def get_pending_doctors(hospital_id: str, skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):

    """Protected endpoint for only hospital admins to check doctors that have not been approved by hospital (pending approval)"""
    if current_user.hospital_uid != hospital_id:
        raise errors.NotAuthorized()
    
    doctors = await doctor_service.get_pending_doctors(hospital_id=hospital_id, skip=skip, limit=limit, session=session)

    return doctors


@doctor_router.patch("/{doctor_id}/status", status_code=status.HTTP_202_ACCEPTED, dependencies=[admin_only])
async def update_doctor_status(doctor_id: str, status: DoctorStatus, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):

    """Protected endpoint for hospital admins to approve doctors after signup"""

    if current_user.admin_type != AdminType.HOSPITAL_ADMIN:
        raise errors.RoleCheckAccess()
    
    
    doctor = await doctor_service.approve_doctor(doctor_id=doctor_id, session=session, status=status)

    if not doctor:
        raise errors.DoctorNotFound()
    
    if doctor.hospital_uid != current_user.hospital_uid:
        raise errors.NotAuthorized()
    
    return doctor


@doctor_router.patch("/{doctor_id}/availability", status_code=status.HTTP_202_ACCEPTED, dependencies=[admin_and_doctor])
async def change_doctor_availability(doctor_id: str, session: AsyncSession = Depends(get_session), current_user: Admin | Doctor = Depends(get_current_user)):

    if current_user.admin_type == AdminType.SUPER_ADMIN:
        raise errors.RoleCheckAccess()
    
    doctor_to_update = await doctor_service.get_doctor(doctor_id=doctor_id, session=session)

    if current_user.hospital_uid != doctor_to_update.hospital_uid:
        raise errors.NotAuthorized
    
    doctor_to_update = await doctor_service.change_doctor_availability(doctor_id=doctor_id, session=session)

    if doctor_to_update is None:
        raise errors.DoctorNotFound
    else:
        return doctor_to_update
    

@doctor_router.patch("/{doctor_id}", status_code=status.HTTP_202_ACCEPTED, dependencies=[doctor_only])
async def update_doctor_profile(doctor_id: str, update_data: DoctorProfileUpdate, session: AsyncSession = Depends(get_session), current_user: Doctor = Depends(get_current_user)):
    """Protected endpoint for updating doctors profile"""

    if current_user.uid != doctor_id:
        raise errors.NotAuthorized()
    
    updated_doctor = await doctor_service.update_doctor_info(doctor_id=doctor_id, update_data=update_data, session=session)

    if updated_doctor is None:
        raise errors.DoctorNotFound()
        
    else:
        return updated_doctor
