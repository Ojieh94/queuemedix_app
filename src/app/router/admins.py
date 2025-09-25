from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import Admin, AdminType, User
from src.app.core.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.app.schemas import AdminProfileUpdate, DoctorAssign
from src.app.services.notification import send_notification
from src.app.services import admins as admin_service, appointment as appt_service
from src.app.database.main import get_session
from src.app.core import permissions
from src.app.core import errors

admin_router = APIRouter(prefix="/admins",
                        tags=['Admins']
                        )
access_token_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(["admin"]))


@admin_router.get('/', response_model=List[User], dependencies=[role_checker])
async def get_admins(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for super admins to get all admins"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    users = await admin_service.get_admins(skip=skip, limit=limit, session=session)

    return users


@admin_router.get('/{admin_id}', dependencies=[role_checker])
async def get_admin(admin_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for super admins to get an admin by uuid"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    user = await admin_service.get_admin(admin_id=admin_id, session=session)

    if user:
        return user
    else:
        raise errors.UserNotFound()
    

@admin_router.patch("/{admin_id}", dependencies=[role_checker])
async def update_admin_profile(admin_id: str, update_data: AdminProfileUpdate, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for updating admin profile"""

    if current_user.uid != admin_id:
        raise errors.NotAuthorized()

    updated_admin = await admin_service.update_admin(admin_id=admin_id, update_data=update_data, session=session)

    if updated_admin is None:
        raise errors.UserNotFound()

    else:
        return updated_admin



@admin_router.delete('/{admin_id}', dependencies=[role_checker])
async def delete_admin(admin_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for super admins to delete admin user"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    admin_to_delete = await admin_service.delete_admin(admin_uid=admin_id, session=session)

    if admin_to_delete is None:
        raise errors.UserNotFound()

    else:
        return {"Message": "Admin deleted successfully"}
    


@admin_router.patch('/appointments/{appointment_uid}', status_code=status.HTTP_202_ACCEPTED)
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
    await send_notification(session, doctor.uid, {
        "title": "Assigned Appointment",
        "body": f"Hello {doctor.full_name}, You have been assigned to {appointment.patient.full_name}'s appointment",
        "data": {"appointment": str(appointment.uid)}
    })

    # Push notification to patient
    await send_notification(session, appointment.patient_uid, {
        "title": "Doctor Assigned",
        "body": f"Your appointment has been assigned to Dr. {doctor.full_name}",
        "data": {"appointment_uid": str(appointment.uid)}
    })

    return {"message": "Doctor assigned successfully!"}
