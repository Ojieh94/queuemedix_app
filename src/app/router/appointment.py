from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from src.app.core.dependencies import RoleChecker, get_current_user
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.schemas import AppointmentCreate, AppointmentRead, DoctorAssign, AppointmentStatusUpdate, MedicalRecordCreate, RescheduleAppointment
from src.app.models import Admin, Doctor, User, Appointment, AppointmentStatus, UserRoles, AdminType
from src.app.services import appointment as apt_service, patients as pat_service, hospital as hp_service, department as dpt_service, medical_records as med_service
from src.app.database.main import get_session
from src.app.core import errors, permissions,mails
from src.app.websocket.appointment_ws import notify_queue_update

"""
create an appointment
list appointments
list patient appointment
get appointment by id
get uncompleted appointment
cancel an appointment
check patient pending appointment
switch apointment status
"""

apt_router = APIRouter(
    tags=['Appointments']
)

admin_and_doctor = Depends(RoleChecker(["doctor", "admin"]))


@apt_router.post('/appointments/new_appointment', status_code=status.HTTP_201_CREATED, response_model=AppointmentRead)
async def add_appointment(patient_uid: str, payload: AppointmentCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Please note, you can not edit an appointment after creating"""

    patient = await pat_service.get_patient(patient_uid, session)

    if not patient:
        raise errors.PatientNotFound()
    
    # Ensure scheduled_time is in the future
    if payload.scheduled_time <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date cannot be in the past.")


    # Check if time slot is available
    time_is_taken = await apt_service.appointment_by_schedule_time(
        payload.hospital_uid, payload.scheduled_time, session)
    
    if time_is_taken:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Time slot is already taken")

    # Check if the patient is already scheduled for an appointment
    existing_appointment = await apt_service.get_patient_pending_appointments(
        patient_uid, session)
    
    if existing_appointment:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Patient already has a pending appointment")

    # Check if the hospital exists
    hospital = await hp_service.get_single_hospital(payload.hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    

    # Check if the department exists
    department = await dpt_service.get_department_by_id(payload.department_uid, session)

    if not department:
        raise errors.DepartmentNotFound()
    
    #access control
    if current_user.role != UserRoles.PATIENT:
        raise errors.NotAuthorized()

    # Create the appointment
    appointment = await apt_service.create_appointment(patient_uid, payload, session)

    #send email to patient
    mails.appointment_success(patient.user.email, patient.user, payload.scheduled_time)

    #send email to hospital
    mails.appointment_notification_hospital(hospital.user.email, patient.user, payload.scheduled_time)

    return appointment



@apt_router.get('/appointments', status_code=status.HTTP_200_OK, response_model=List[AppointmentRead])
async def get_appointments(status: Optional[AppointmentStatus], skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    appointments = await apt_service.get_appointments(skip, limit, status, session)

    #admin level control
    if current_user.admin.admin_type != AdminType.SUPER_ADMIN:
        raise errors.NotAuthorized()

    return appointments


@apt_router.get('/appointments/{patient_uid}/appointments', status_code=status.HTTP_200_OK, response_model=List[AppointmentRead])
async def get_patient_appointments(patient_uid: str, skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    patient = await pat_service.get_patient(patient_uid, session)
    
    if not patient:
        raise errors.PatientNotFound()

    appointments = await apt_service.get_patient_appointments(patient_uid, skip, limit, session)

    #access control
    return permissions.access_grant_for_patient_appointments(current_user, patient, appointments)
    

@apt_router.get('/appointments/{hospital_id}/appointments', status_code=status.HTTP_200_OK, response_model=List[Appointment])
async def get_hospital_appointments(hospital_uid: int, skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    appointments = await apt_service.get_hospital_appointments(hospital_uid, skip, limit, session)

    #access control
    return permissions.access_grant_for_hospital_appointments(current_user, appointments)


@apt_router.get('/appointments/uncompleted_appointments', status_code=status.HTTP_200_OK, response_model=List[Appointment])
async def get_uncompleted_appointments(session: AsyncSession = Depends(get_session), current_user: User=Depends(get_current_user)):

    appointments = await apt_service.get_uncompleted_appointments(session)

    #access control
    permissions.general_access_list(current_user, appointments)

    return appointments



@apt_router.get('/appointments/pending_appointments', status_code=status.HTTP_200_OK, response_model=List[Appointment])
async def get_all_pending_appointments(session: AsyncSession = Depends(get_session), current_user: User=Depends(get_current_user)):

    appointments = await apt_service.get_all_pending_appointments(session)

    #access control
    permissions.general_access_list(current_user, appointments)

    return appointments



@apt_router.get('/appointments/{appointment_uid}', status_code=status.HTTP_200_OK, response_model=Appointment)
async def get_appointment_by_id(appointment_uid: str, session: AsyncSession = Depends(get_session), current_user: User=Depends(get_current_user)):

    appointment = await apt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()
    
    #access control
    permissions.general_access(current_user, appointment)

    return appointment


@apt_router.patch('/appointments/{appointment_uid}/cancel', status_code=status.HTTP_202_ACCEPTED)
async def cancel_appointment(appointment_uid: str, session: AsyncSession = Depends(get_session), current_user: User=Depends(get_current_user)):

    appointment = await apt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()
 
    if appointment.status == AppointmentStatus.CANCELED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment is already canceled")
    
    #access control
    if current_user.uid != appointment.patient.user_uid:
        raise errors.NotAuthorized()
    
    await apt_service.cancel_appointment(appointment_uid, session)

    await notify_queue_update(session, appointment.hospital_uid)

    #send email to patient
    mails.appointment_canceled(appointment.patient.user.email, appointment.patient.user, appointment.scheduled_time)

    return {"message": "Appointment has been cancelled successfully!"}


#set appointment status
@apt_router.put('/appointments/{appointment_uid}/appointment_status', status_code=status.HTTP_200_OK)
async def update_appointment_status(appointment_uid: str, new_status: AppointmentStatusUpdate, session: AsyncSession = Depends(get_session), current_user: User=Depends(get_current_user)):

    appointment = await apt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()
    
    #acces control
    permissions.check_appointment_access(current_user, appointment)

    await apt_service.switch_appointment_status(appointment_uid, new_status, session)

    await notify_queue_update(session, appointment.hospital_uid)

    return {"message": f"Appointment status has been updated to {new_status.status}"}



@apt_router.delete('/appointments/{appointment_uid}/delete', status_code=status.HTTP_204_NO_CONTENT)
async def delete_db_appointment(appointment_uid: str, session: AsyncSession = Depends(get_session), current_user: User=Depends(get_current_user)):

    appointment = await apt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()
    
    #access control
    if current_user.uid != appointment.patient.user_uid:
        raise errors.NotAuthorized()
    
    await apt_service.delete_appointment(appointment_uid, session)


# #############################-----------###################
@apt_router.post('/appointments/{appointment_id}/medical_records', dependencies=[admin_and_doctor], status_code=status.HTTP_201_CREATED)
async def create_medical_record(appointment_id: str, payload: MedicalRecordCreate, session: AsyncSession = Depends(get_session), current_user: Admin | Doctor = Depends(get_current_user)):
    """

        This endpoint is for doctors or hospital admin to create medical records, these entities will create the medical records from the appointment routes so that doctor id, patient id and hospital id are automatically assigned to medical records from the appointment details
    
    """
    if current_user.admin_type == AdminType.SUPER_ADMIN:
        raise errors.NotAuthorized()

    appointment = await apt_service.get_appointment_by_id(appointment_uid=appointment_id, session=session)

    if appointment is None:
        raise errors.AppointmentNotFound()

    if current_user.hospital_uid != appointment.hospital_uid:
        raise errors.NotAuthorized()

    payload.hospital_uid = appointment.hospital_uid
    payload.patient_uid = appointment.patient_uid
    payload.doctor_uid = appointment.doctor_uid

    new_record = await med_service.create_medical_record(payload=payload, session=session)

    return new_record


#reschedule appointment
@apt_router.put("/appointments/{appointment_uid}/reschedule")
async def reschedule_appointment(
    appointment_uid: str,
    payload: RescheduleAppointment,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):

    appointment = await apt_service.get_appointment_by_id(appointment_uid, session)

    if not appointment:
        raise errors.AppointmentNotFound()

    # Ensure scheduled_time is in the future
    if payload.new_time <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date cannot be in the past.")

    # Check if time slot is available
    time_is_taken = await apt_service.appointment_by_schedule_time(
        appointment.hospital_uid, payload.new_time, session)
    
    if time_is_taken:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Time slot is already taken")
    
    #access control
    permissions.appointment_reschedule_access(current_user, appointment)

    await apt_service.reschedule_appointment(appointment_uid, payload, session, current_user)

    #inform the patient through email
    mails.appointment_rescheduled(appointment.patient.user.email, appointment.patient.full_name, appointment.hospital.hospital_name, appointment.scheduled_time, payload.new_time)

    return {
        "message": "Appointment rescheduled successfully",
        "appointment": appointment
    }