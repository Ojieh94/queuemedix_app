from typing import List
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import Admin, AdminType, User, UserRoles
from src.app.core.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.app.schemas import AdminProfileUpdate, AdminRead, DoctorAssign, VerifyHospital
from src.app.services.notification import send_notification
from src.app.services import admins as admin_service, appointment as appt_service, hospital as hp_service
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
async def get_admin(admin_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Protected endpoint for super admins to get an admin by uuid"""

    permissions.accessible_to_super_admin(current_user)

    admin = await admin_service.get_admin(admin_id=admin_id, session=session)

    if admin:
        return admin
    else:
        raise errors.AdminNotFound()
    

@admin_router.get('/hospitals/{hospital_id}/admins', status_code=status.HTTP_200_OK ,response_model=List[AdminRead])
async def get_hospital_admins(hospital_id: str, skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    """Protected endpoint for super admins and hospital admins to get all admins of a hospital"""

    if current_user.role not in [UserRoles.ADMIN, UserRoles.HOSPITAL]:
        raise errors.NotAuthorized()
    
    if current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
        if current_user.admin.hospital_uid != uuid.UUID(hospital_id):
            raise errors.NotAuthorized()
        
    if current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital.uid != uuid.UUID(hospital_id):
            raise errors.NotAuthorized()

    admins = await admin_service.get_hospital_admins(hospital_id=hospital_id, session=session)

    return admins
    

@admin_router.put("/admins/{admin_id}", status_code=status.HTTP_202_ACCEPTED, response_model=AdminRead)
async def update_admin_profile(admin_id: str, update_data: AdminProfileUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Protected endpoint for updating admin profile"""

    if current_user.role != UserRoles.ADMIN or current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN:
        raise errors.NotAuthorized()
    
    admin_to_update = await admin_service.get_admin(admin_id, session)

    if not admin_to_update:
        raise errors.AdminNotFound()
    
    if current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
        if current_user.admin.hospital_uid != admin_to_update.hospital_uid:
            
            raise errors.NotAuthorized()
    
    admin = await admin_service.update_admin(admin_id, update_data, session)

    return admin

    
    


@admin_router.delete("/admins/{admin_id}", status_code=status.HTTP_200_OK)
async def delete_admin(
    admin_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Protected endpoint for super admins (and hospital admins) to delete admin users"""

    # Ensure only admins of correct types can delete
    if (
        current_user.role != UserRoles.ADMIN
        or current_user.admin.admin_type not in [AdminType.HOSPITAL_ADMIN, AdminType.SUPER_ADMIN]
    ):
        raise errors.NotAuthorized()

    # Fetch admin to delete
    admin_to_delete = await admin_service.get_admin(admin_id=admin_id, session=session)
    if not admin_to_delete:
        raise errors.AdminNotFound()

    # Hospital admins can only delete admins within their own hospital
    if (
        current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN
        and admin_to_delete.hospital_uid != current_user.admin.hospital_uid
    ):
        raise errors.NotAuthorized()

    # Perform deletion
    await admin_service.delete_admin(admin_id=admin_id, session=session)

    return {"message": "Admin deleted successfully"}




@admin_router.patch('/appointments/{appointment_uid}/admin', status_code=status.HTTP_202_ACCEPTED)
async def assign_doctor(appointment_uid: str, payload: DoctorAssign, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    appointment = await appt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()
    
    #access control
    permissions.doctor_assign_access(current_user, appointment)

    
    #Check if the doctor is available...............(awaiting doctor's service)
    doctor = await appt_service.get_single_doctor(payload.doctor_uid, session)

    if not doctor:
        raise errors.DoctorNotFound()
    
    if not doctor.is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor is currently unavailable")
    
    # Assign doctor to the appointment
    appointment.doctor_uid = payload.doctor_uid
    await session.commit()
    await session.refresh(appointment)

    #push notification to doctor
    await send_notification(session, doctor.user_uid, {
        "title": "Assigned Appointment",
        "body": f"Hello {doctor.full_name}, You have been assigned to {appointment.patient.full_name}'s appointment",
        "data": {"appointment": str(appointment.uid)}
    })

    # Push notification to patient
    await send_notification(session, appointment.patient.user_uid, {
        "title": "Doctor Assigned",
        "body": f"Your appointment has been assigned to Dr. {doctor.full_name}",
        "data": {"appointment_uid": str(appointment.uid)}
    })

    return {"message": "Doctor assigned successfully!"}


@admin_router.patch('/hospitals/{hospital_uid}/admin', status_code=status.HTTP_200_OK)
async def approve_hospital(hospital_uid: str, payload: VerifyHospital, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    
    if not hospital:
        raise errors.HospitalNotFound()
    
    #access control
    if current_user.admin.admin_type != AdminType.SUPER_ADMIN:
        raise errors.NotAuthorized()
    
    #approve/reject hospital application
    await hp_service.approve_hospital(hospital_uid, payload, session)

    return {"message": "Your request has been recorded successfully."}
    
