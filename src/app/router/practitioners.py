# from pydoc import doc
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import AdminType, PractitionerStatus, User, UserRoles, PractitionerType
from src.app.core.dependencies import AccessTokenBearer, get_current_user
from src.app.schemas import PractitionerProfileUpdate, PractitionerRead
from src.app.services import practitioners as pract_services
from src.app.database.main import get_session
from src.app.core import errors

practitioner_router = APIRouter(prefix="/practitioners", tags=["practitioners"])
access_token_bearer = AccessTokenBearer()



@practitioner_router.get("/search", status_code=status.HTTP_200_OK, response_model=List[PractitionerRead])
async def search_practitioners(
    q: str = Query(None, description="Search text (name, specialty, bio)"),
    specialty: str = "",
    hospital_id: str = "",
    is_available: bool = False,
    status: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    sort_by: str = "last_name",
    sort_dir: str = "asc",
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Protected endpoint for admins to search practitioners"""

    # allow access to own hospitals
    is_hospital = (
        current_user.hospital is not None
        and current_user.hospital.uid == hospital_id
    )

    is_super_admin = (
        current_user.admin is not None
        and current_user.role == UserRoles.ADMIN
        and current_user.admin.admin_type == AdminType.SUPER_ADMIN
    )

    is_hospital_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type in [
            AdminType.DEPARTMENT_ADMIN,
            AdminType.HOSPITAL_ADMIN,
        ]
        and current_user.admin.hospital_uid == hospital_id
    )

    if not (is_hospital or is_super_admin or is_hospital_admin):
        raise errors.NotAuthorized()
        
    result = await pract_services.search_practitioner(
        session=session,
        q=q,
        specialization=specialty,
        hospital_id=hospital_id,
        is_available=is_available,
        status=status,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    return result


@practitioner_router.get(
    "/", response_model=List[PractitionerRead], status_code=status.HTTP_200_OK
)
async def get_all_practitioners(
    skip: int = 0,
    limit: int = 10,
    practioner_type: PractitionerType | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
   
    
    """Protected endpoint for super admins to get all practitioners"""
    if current_user.role != UserRoles.ADMIN:
        raise errors.RoleCheckAccess()

    if (
        current_user.admin is None
        or current_user.admin.admin_type != AdminType.SUPER_ADMIN
    ):
        raise errors.NotAuthorized()
    

    practitioners = await pract_services.get_all_practitioners(
        skip=skip, limit=limit, practitioner_type=practioner_type, session=session
    )

    return practitioners


@practitioner_router.get('/practitioner', status_code=status.HTTP_200_OK, response_model=PractitionerRead)
async def get_practitioner(practitioner_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    """Protected endpoint to get a doctor by uuid"""


    practitioner = await pract_services.get_practitioner(practitioner_id=practitioner_id, session=session)

    if not practitioner:
        raise errors.PractitionerNotFound()

    is_practitioner = (
        current_user.practitioner is not None
        and current_user.practitioner.uid == practitioner.uid
    )

    is_hospital = (
        current_user.hospital is not None
        and current_user.hospital.uid == practitioner.hospital_uid
    )

    if not (is_practitioner or is_hospital):
        raise errors.NotAuthorized()

    return practitioner
    

@practitioner_router.get("/pending-practitioners", status_code=status.HTTP_200_OK, response_model=List[PractitionerRead])
async def get_pending_practitioners(hospital_id: str, skip: int = 0, limit: int = 10, type: PractitionerType | None = None, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Protected endpoint for only hospital and their admins to check doctors that have not been approved by hospital (pending approval)"""
    
    is_hospital_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN
        and current_user.admin.hospital_uid == hospital_id
    )

    is_department_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN
        and current_user.admin.hospital_uid == hospital_id
    )

    is_hospital = (
        current_user.hospital is not None and current_user.hospital.uid == hospital_id
    )

    if not (is_hospital or is_hospital_admin or is_department_admin):
        raise errors.NotAuthorized()

    pending_practitioners = await pract_services.get_pending_practitioners(hospital_id=hospital_id, type=type, skip=skip, limit=limit, session=session)

    return pending_practitioners


@practitioner_router.patch("/practitioner-status", status_code=status.HTTP_202_ACCEPTED)
async def update_practitioner_status(practitioner_id: str, status: PractitionerStatus, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Protected endpoint for hospital admins and hospital to approve practitioners after vetting
    
    status:'under_review', 'approved', 'rejected', 'suspended'
    """

    practitioner = await pract_services.get_practitioner(practitioner_id=practitioner_id, session=session)

    if not practitioner:
        raise errors.PractitionerNotFound()

    is_hospital_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN
        and current_user.admin.hospital_uid == practitioner.hospital_uid
    )

    is_department_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN
        and current_user.admin.hospital_uid == practitioner.hospital_uid
    )

    is_hospital = (
        current_user.hospital is not None and current_user.hospital.uid == practitioner.hospital_uid
    )

    if not (is_hospital or is_hospital_admin or is_department_admin):
        raise errors.NotAuthorized()
    

    await pract_services.approve_practitioner(practitioner_id=practitioner_id, session=session, status=status)
    
    return {"message": f"The Practitioner has been successfully updated to {practitioner.status.value}"}


@practitioner_router.patch("/availability", status_code=status.HTTP_202_ACCEPTED)
async def change_practitioner_availability(practitioner_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Protected endpoint for hospital admins, department admins and hospitals, self-practitioners to change practitioners availability
    """

    # if current_user.role not in [UserRoles.ADMIN, UserRoles.HOSPITAL, UserRoles.DOCTOR]:
    #     raise errors.RoleCheckAccess()
    
    practitioner_to_update = await pract_services.get_practitioner(practitioner_id=practitioner_id, session=session)

    if not practitioner_to_update:
        raise errors.PractitionerNotFound()


    is_practitioner = (
        current_user.practitioner is not None
        and current_user.practitioner.uid == practitioner_to_update.uid
    )
    
    is_super_admin = (
        current_user.admin is not None 
        and current_user.admin.admin_type == AdminType.SUPER_ADMIN
    )
    
    is_hospital_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN
        and current_user.admin.hospital_uid == practitioner_to_update.hospital_uid
    )

    is_department_admin = (
        current_user.admin is not None
        and current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN
        and current_user.admin.hospital_uid == practitioner_to_update.hospital_uid
    )

    is_hospital = (
        current_user.hospital is not None and current_user.hospital.uid == practitioner_to_update.hospital_uid
    )

    if not (is_practitioner or is_super_admin or is_hospital or is_hospital or is_hospital_admin or is_department_admin):
        raise errors.NotAuthorized()
    
    await pract_services.change_practitioner_availability(practitioner_id=practitioner_id, session=session)

    return {"message": "Availabilty updated successfully"}
    
    

@practitioner_router.patch("/profile-update", status_code=status.HTTP_202_ACCEPTED, response_model=PractitionerRead)
async def update_practitioner_profile(practitioner_id: str, update_data: PractitionerProfileUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Protected endpoint for updating doctors profile"""

    if current_user.role != UserRoles.PRACTITIONER:
        raise errors.RoleCheckAccess()

    
    practitioner_to_update = await pract_services.get_practitioner(practitioner_id=practitioner_id, session=session)

    if not practitioner_to_update:
        raise errors.PractitionerNotFound()
    
    is_practitioner = (
        current_user.practitioner is not None
        and current_user.practitioner.uid == practitioner_to_update.uid
    )

    if not is_practitioner:
        raise errors.NotAuthorized()
    
    updated_practitioner = await pract_services.update_practitioner_info(practitioner_id, update_data, session)
    
    return updated_practitioner

