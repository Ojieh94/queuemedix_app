from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List, Optional
from src.app.models import Appointment, AppointmentStatus, Doctor, User, RescheduleHistory
from src.app.schemas import AppointmentCreate, AppointmentStatusUpdate, RescheduleAppointment
from src.app.websocket.appointment_ws import notify_queue_update
from src.app.services.notification import send_notification
from src.app.core import mails

"""
create an appointment
list appointments
list patient appointment
get appointment by id
get appointment by hospital
get uncompleted appointment
cancel an appointment
check pending appointment
switch apointment status
"""

async def create_appointment(patient_uid: str, payload: AppointmentCreate, session: AsyncSession):
    
    new_appt = Appointment(**payload.model_dump(), patient_uid=patient_uid)

    session.add(new_appt)
    await session.commit()
    await session.refresh(new_appt)
    
    # Broadcast updated queue (real-time to hospital staff)
    await notify_queue_update(hospital_uid=new_appt.hospital_uid, session=session)

    # Notify hospital
    await send_notification(session, new_appt.hospital.user_uid, {
        "title": "New Appointment",
        "body": f"You have a new appointment with {new_appt.patient.full_name}",
        "data": {"appointment_uid": str(new_appt.uid)}
    })

    # Notify patient
    await send_notification(session, new_appt.patient.user_uid, {
        "title": "Appointment Scheduled",
        "body": f"Your appointment has been booked with {new_appt.hospital.hospital_name}",
        "data": {"appointment_uid": str(new_appt.uid)}
    })

    return new_appt 


# async def update_appointment(appointment_uid: str, payload: AppointmentUpdate, session: AsyncSession):

#     appointment_to_update = await get_appointment_by_id(appointment_uid, session)

#     if appointment_to_update:

#         appointment_dict = payload.model_dump(exclude_unset=True)

#         for k, v in appointment_dict.items():
#             setattr(appointment_to_update, k, v)

#         await session.commit()
#         await session.refresh(appointment_to_update)

#         return appointment_to_update
    
#     else:
#         return None
    

async def get_appointments(skip: int, limit: int, status: Optional[AppointmentStatus], session: AsyncSession) -> List[Appointment]:

    stmt = select(Appointment).order_by(Appointment.scheduled_time).offset(skip).limit(limit)

    if status is not None:
        stmt = stmt.where(Appointment.status == status)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_patient_appointments(patient_uid: str, skip: int, limit: int, session: AsyncSession) -> List[Appointment]:

    stmt = select(Appointment).where(Appointment.patient_uid == patient_uid).order_by(Appointment.scheduled_time).offset(skip).limit(limit)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_appointment_by_id(appointment_uid: str, session: AsyncSession) -> Appointment:

    return (await session.execute(select(Appointment).where(Appointment.uid == appointment_uid))).scalar_one_or_none()


async def get_hospital_appointments(hospital_uid: str, skip: int, limit: int, session: AsyncSession) -> List[Appointment]:

    stmt = select(Appointment).where(Appointment.hospital_uid == hospital_uid).order_by(Appointment.scheduled_time).offset(skip).limit(limit)

    result = await session.execute(stmt)

    return result.scalars().all()


async def appointment_by_schedule_time(hospital_uid: str, scheduled_time: str, session: AsyncSession) ->Appointment:

    stmt = select(Appointment).where(Appointment.hospital_uid == hospital_uid, Appointment.scheduled_time == scheduled_time)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_uncompleted_appointments(session: AsyncSession) -> List[Appointment]:

    stmt = select(Appointment).where(Appointment.status != AppointmentStatus.COMPLETED).order_by(Appointment.scheduled_time)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_single_doctor(doctor_uid: str, session: AsyncSession) -> Doctor:

    stmt = select(Doctor).where(Doctor.uid == doctor_uid)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()



async def cancel_appointment(appointment_uid: int, session: AsyncSession):
    
    appointment = await get_appointment_by_id(appointment_uid, session)
    
    if not appointment:
        return None
    
    appointment.status = AppointmentStatus.CANCELED
    await session.commit()
    await session.refresh(appointment)

    return appointment


async def get_all_pending_appointments(session: AsyncSession) -> List[Appointment]:
    
    stmt = select(Appointment).where(Appointment.status == AppointmentStatus.PENDING).order_by(Appointment.scheduled_time)

    result = await session.execute(stmt)

    return result.scalars().all()



async def get_patient_pending_appointments(patient_uid: str, session: AsyncSession) -> Appointment:

    stmt = select(Appointment).where(Appointment.patient_uid == patient_uid, Appointment.status != AppointmentStatus.COMPLETED)
    
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def switch_appointment_status(appointment_uid: str, new_status: AppointmentStatusUpdate, session: AsyncSession) -> Appointment:

    appointment = await get_appointment_by_id(appointment_uid, session)
    
    if not appointment:
        return None
    
    appointment.status = new_status.status

    await session.commit()
    await session.refresh(appointment)

    return appointment


async def delete_appointment(appointment_uid: str, session: AsyncSession):

    appointment = await get_appointment_by_id(appointment_uid, session)
    
    if not appointment:
        return None
    
    await session.delete(appointment)
    await session.commit()

    await notify_queue_update(session, appointment.hospital_uid)


async def reschedule_appointment(
    appointment_uid: str,
    payload: RescheduleAppointment,
    session: AsyncSession,
    current_user: User,  # returns dict with id, role, etc.
):
    # Fetch appointment
    appointment = await get_appointment_by_id(appointment_uid, session)
    if not appointment:
        return None

    old_time = appointment.scheduled_time
    appointment.scheduled_time = payload.new_time
    appointment.status = AppointmentStatus.RESCHEDULED
    appointment.rescheduled_from = old_time  #for current state tracking

    # Log the history
    history = RescheduleHistory(
        appointment_uid=appointment.uid,
        old_time=old_time,
        new_time=payload.new_time,
        reason=payload.reason,
        rescheduled_by_id=current_user.uid,
    )
    session.add(history)

    await session.commit()
    await session.refresh(appointment)

    # Notify patient
    await send_notification(session, appointment.patient.user_uid, {
        "title": "Appointment Rescheduled",
        "body": f"Your appointment with {appointment.hospital.hospital_name}, has been rescheduled to {payload.new_time}",
        "data": {"appointment_uid": str(appointment.uid)}
    })
    
    return appointment
