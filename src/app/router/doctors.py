from pydoc import doc
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import AdminType, Doctor, DoctorStatus, User, UserRoles
from src.app.core.dependencies import AccessTokenBearer, get_current_user
from src.app.schemas import DoctorProfileUpdate, DoctorRead
from src.app.services import doctors as doctor_service
from src.app.database.main import get_session
from src.app.core import errors

doctor_router = APIRouter(prefix="/doctors", tags=["doctors"])
access_token_bearer = AccessTokenBearer()



@doctor_router.get("/search", status_code=status.HTTP_200_OK, response_model=List[DoctorRead])
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
    current_user: User = Depends(get_current_user),
):
    """Protected endpoint for admins to search doctors"""

    if current_user.role != UserRoles.ADMIN:
        raise errors.RoleCheckAccess()

    # Super admin → unrestricted
    if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
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
        if hospital_id and current_user.admin.hospital_uid != hospital_id:
            raise errors.NotAuthorized()

        result = await doctor_service.search_doctors(
            session=session,
            q=q,
            specialty=specialty,
            hospital_id=current_user.admin.hospital_uid,  # enforce hospital scope
            is_available=is_available,
            status=status,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    return result


@doctor_router.get('/', response_model=List[Doctor], status_code=status.HTTP_200_OK)
async def get_all_doctors(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: User = Depends(get_current_user)):

    """Protected endpoint for super admins to get all doctors"""
    if current_user.role != UserRoles.ADMIN:
        raise errors.NotAuthorized()

    if current_user.admin.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    doctors = await doctor_service.get_all_doctors(skip=skip, limit=limit, session=session)

    return doctors


@doctor_router.get('/{doctor_id}', status_code=status.HTTP_200_OK, response_model=DoctorRead)
async def get_doctor(doctor_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    """Protected endpoint to get a doctor by uuid"""

    if current_user.role != UserRoles.DOCTOR:
        raise errors.RoleCheckAccess()

    doctor = await doctor_service.get_doctor(doctor_id=doctor_id, session=session)

    if not doctor:
        raise errors.DoctorNotFound()
    
    if current_user.doctor.uid != doctor.uid:
        raise errors.NotAuthorized()
    
    return doctor
    

@doctor_router.get("/{hospital_id}", status_code=status.HTTP_200_OK, response_model=List[DoctorRead])
async def get_pending_doctors(hospital_id: str, skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Protected endpoint for only hospital admins to check doctors that have not been approved by hospital (pending approval)"""
    if current_user.role != UserRoles.ADMIN:
        raise errors.RoleCheckAccess()
    
    if current_user.admin.admin_type != AdminType.HOSPITAL_ADMIN:
        raise errors.RoleCheckAccess()
    
    if current_user.admin.hospital_uid != hospital_id:
        raise errors.NotAuthorized()
    
    pending_doctors = await doctor_service.get_pending_doctors(hospital_id=hospital_id, skip=skip, limit=limit, session=session)

    return pending_doctors


@doctor_router.patch("/{doctor_id}/status", status_code=status.HTTP_202_ACCEPTED)
async def update_doctor_status(doctor_id: str, status: DoctorStatus, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Protected endpoint for hospital admins to approve doctors after signup"""

    if current_user.role != UserRoles.ADMIN:
        raise errors.RoleCheckAccess()

    if current_user.admin.admin_type != AdminType.HOSPITAL_ADMIN:
        raise errors.RoleCheckAccess()
    
    
    doctor = await doctor_service.get_doctor(doctor_id=doctor_id, session=session)

    if not doctor:
        raise errors.DoctorNotFound()
    
    if doctor.hospital_uid != current_user.admin.hospital_uid:
        raise errors.NotAuthorized()
    
    approved_doctor = await doctor_service.approve_doctor(doctor_id=doctor_id, session=session, status=status)

    return approved_doctor


@doctor_router.patch("/{doctor_id}/availability", status_code=status.HTTP_202_ACCEPTED, response_model=DoctorRead)
async def change_doctor_availability(doctor_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Protected endpoint for hospital admins, department admins and doctors to change doctor's availability"""

    if current_user.role not in [UserRoles.ADMIN, UserRoles.DOCTOR]:
        raise errors.RoleCheckAccess()
    
    doctor_to_update = await doctor_service.get_doctor(doctor_id=doctor_id, session=session)

    if not doctor_to_update:
        raise errors.DoctorNotFound()
    
    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            raise errors.NotAuthorized()
        
        elif current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
            if doctor_to_update.hospital_uid != current_user.admin.hospital_uid:
                raise errors.NotAuthorized()
        
        elif current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN:
            if doctor_to_update.department_uid != current_user.admin.department_uid:
                raise errors.NotAuthorized()
    
    doctor_to_update = await doctor_service.change_doctor_availability(doctor_id=doctor_id, session=session)

    return doctor_to_update
    
    

@doctor_router.patch("/{doctor_id}", status_code=status.HTTP_202_ACCEPTED, response_model=DoctorRead)
async def update_doctor_profile(doctor_id: str, update_data: DoctorProfileUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Protected endpoint for updating doctors profile"""

    if current_user.role != UserRoles.DOCTOR:
        raise errors.RoleCheckAccess()

    
    doctor_to_update = await doctor_service.get_doctor(doctor_id=doctor_id, session=session)
    
    if current_user.doctor.uid != doctor_to_update.uid:
        raise errors.NotAuthorized()

    if not doctor_to_update:
        raise errors.DoctorNotFound()
    
    updated_doctor = await doctor_service.update_doctor_info(doctor_id, update_data, session)
    
    return updated_doctor

