from typing import List
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import  AdminType, User, UserRoles, AppointmentStatus
from src.app.core.dependencies import AccessTokenBearer, get_current_user
from src.app.schemas import AdminProfileUpdate, AdminRead, PractitionerAssign, VerifyHospital
from src.app.services.notification import send_notification
from src.app.services import admins as admin_service, appointment as appt_service, hospital as hp_service, queue
from src.app.database.main import get_session
from src.app.core import permissions
from src.app.core import errors

admin_router = APIRouter(tags=['Admins'])
access_token_bearer = AccessTokenBearer()



@admin_router.get('/admins', status_code=status.HTTP_200_OK ,response_model=List[AdminRead])
async def get_admins(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    """Protected endpoint for super admins to get all admins"""

    permissions.accessible_to_super_admin(current_user)

    users = await admin_service.get_admins(skip=skip, limit=limit, session=session)

    return users


@admin_router.get('/admins/{admin_id}', status_code=status.HTTP_200_OK, response_model=AdminRead)
async def get_admin(admin_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Protected endpoint for super admins to get an admin by uuid"""

    permissions.accessible_to_super_admin(current_user)

    admin = await admin_service.get_admin(admin_uid, session)

    if admin:
        return admin
    else:
        raise errors.AdminNotFound()
    

@admin_router.get('/hospitals/admins', status_code=status.HTTP_200_OK ,response_model=List[AdminRead])
async def get_hospital_admins(hospital_uid: uuid.UUID, skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    """Protected endpoint for super admins and hospital admins to get all admins of a hospital"""

    if current_user.role not in [UserRoles.ADMIN, UserRoles.HOSPITAL]:
        raise errors.RoleCheckAccess()
    
    is_hospital_admin = (current_user.admin is not None and current_user.admin.hospital_uid == hospital_uid)

    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_uid)

    is_admin = (current_user.admin is not None and current_user.admin.admin_type == AdminType.SUPER_ADMIN)
        
    if not (is_hospital or is_hospital_admin or is_admin):
        raise errors.NotAuthorized()

    admins = await admin_service.get_hospital_admins(hospital_uid, session)

    return admins
    

@admin_router.put("/admins/profile-update", status_code=status.HTTP_202_ACCEPTED, response_model=AdminRead)
async def update_admin_profile(admin_uid: uuid.UUID, update_data: AdminProfileUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Protected endpoint for updating admin profile"""
    
    admin_to_update = await admin_service.get_admin(admin_uid, session)

    if not admin_to_update:
        raise errors.AdminNotFound()
    
    if current_user.uid != admin_to_update.user_uid:
        raise errors.NotAuthorized()
    
    admin = await admin_service.update_admin(admin_uid, update_data, session)

    return admin

    
    


@admin_router.delete("/admins/delete-account", status_code=status.HTTP_200_OK)
async def delete_admin(
    admin_uid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Protected endpoint for super admins (and hospital admins) to delete admin users"""

     # Fetch admin to delete
    admin_to_delete = await admin_service.get_admin(admin_uid, session)
    if not admin_to_delete:
        raise errors.AdminNotFound()

    # Ensure only admins of correct types can delete
    is_hospital_admin = (current_user.admin is not None and current_user.admin.hospital_uid == admin_to_delete.hospital_uid)

    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == admin_to_delete.hospital_uid)

    is_admin = (current_user.admin is not None and current_user.admin.admin_type == AdminType.SUPER_ADMIN)
        
    if not (is_hospital or is_hospital_admin or is_admin):
        raise errors.NotAuthorized()

   

    # Perform deletion
    await admin_service.delete_admin(admin_uid, session)

    return {"message": "Admin deleted successfully"}




@admin_router.patch('/appointments/assign-practitioner', status_code=status.HTTP_202_ACCEPTED)
async def assign_practitioner(appointment_uid: uuid.UUID, payload: PractitionerAssign, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    appointment = await appt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()
    
    #access control
    permissions.practitioner_assign_access(current_user, appointment)

    
    #Check if the practitioner is available...............(awaiting practitioner's service)
    practitioner = await appt_service.get_single_practitioner(payload.practitioner_uid, session)

    if not practitioner:
        raise errors.PractitionerNotFound()
    
    if not practitioner.is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected practitioner is currently unavailable")
    
    # Assign practitioner to the appointment
    appointment.practitioner_uid = payload.practitioner_uid
    appointment.status = AppointmentStatus.IN_PROGRESS

    # Create queue entry
    await queue.create_queue_entry(appointment, session)

    await session.commit()
    await session.refresh(appointment)

    practitioner_full_name = " ".join(filter(None, [practitioner.first_name, practitioner.last_name]))

   
    #push notification to practitioner
    await send_notification(session, practitioner.user_uid, {
        "title": "Assigned Appointment",
        "body": f"Hello {practitioner_full_name}, You have been assigned to {appointment.patient.first_name}'s appointment",
        "data": {"appointment": appointment.uid}
    })

    # Push notification to patient
    await send_notification(session, appointment.patient.user_uid, {
        "title": " Assigned",
        "body": f"Your appointment has been assigned to {practitioner.title}. {practitioner_full_name}",
        "data": {"appointment_uid": str(appointment.uid)}
    })

    return {"message": "Practitioner assigned successfully!"}


@admin_router.patch('/hospitals/approve-hospital', status_code=status.HTTP_200_OK)
async def approve_hospital(hospital_uid: uuid.UUID, payload: VerifyHospital, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    
    if not hospital:
        raise errors.HospitalNotFound()
    
    #access control
    if (current_user.admin is not None and current_user.admin.admin_type != AdminType.SUPER_ADMIN):
        raise errors.NotAuthorized()
    
    #approve/reject hospital application
    await hp_service.approve_hospital(hospital_uid, payload, session)

    return {"message": "Your request has been recorded successfully."}
    
