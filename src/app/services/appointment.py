import uuid
from collections.abc import Sequence
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from datetime import datetime, timezone, timedelta
from sqlalchemy import update
from typing import Any, List, Optional
from src.app.models import Appointment, AppointmentStatus, Practitioner, User, RescheduleHistory, Hospital, Patient
from src.app.schemas import AppointmentCreate, AppointmentStatusUpdate, RescheduleAppointment
from src.app.websocket.appointment_ws import notify_queue_update
from src.app.services.notification import send_notification
# from src.app.core import mails

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

async def create_appointment(patient_uid: uuid.UUID, payload: AppointmentCreate, session: AsyncSession):
    
    new_appt = Appointment(**payload.model_dump(), patient_uid=patient_uid)

    session.add(new_appt)
    await session.commit()
    await session.refresh(new_appt)
    
    # Broadcast updated queue (real-time to hospital staff)
    await notify_queue_update(hospital_uid=new_appt.hospital_uid, session=session)

    # Notify hospital
    await send_notification(session, new_appt.hospital.user_uid, {
        "title": "New Appointment",
        "body": f"You have a new appointment with {new_appt.patient.first_name} {new_appt.patient.last_name}",
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
    

async def get_appointments(skip: int, limit: int, status: Optional[AppointmentStatus], session: AsyncSession) -> Sequence[Appointment]:

    stmt = select(Appointment).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    ).order_by(Appointment.scheduled_time).offset(skip).limit(limit) #type: ignore

    if status is not None:
        stmt = stmt.where(Appointment.status == status)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_patient_appointments(patient_uid: uuid.UUID, skip: int, limit: int, session: AsyncSession) -> Sequence[Appointment]:

    stmt = select(Appointment).where(Appointment.patient_uid == patient_uid).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    ).order_by(Appointment.scheduled_time).offset(skip).limit(limit) #type: ignore

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_appointment_by_id(appointment_uid: uuid.UUID, session: AsyncSession) -> Appointment | None:

    return (await session.execute(select(Appointment).where(Appointment.uid == appointment_uid).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    ))).scalar_one_or_none()


async def get_hospital_appointments(hospital_uid: uuid.UUID, skip: int, limit: int, session: AsyncSession) -> Sequence[Appointment]:

    stmt = select(Appointment).where(Appointment.hospital_uid == hospital_uid).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    ).order_by(Appointment.scheduled_time).offset(skip).limit(limit) #type: ignore

    result = await session.execute(stmt)

    return result.scalars().all()


async def appointment_by_schedule_time(hospital_uid: uuid.UUID, scheduled_time: datetime, session: AsyncSession) ->Appointment | None:

    stmt = select(Appointment).where(Appointment.hospital_uid == hospital_uid, Appointment.scheduled_time == scheduled_time).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    )

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_uncompleted_appointments(hospital_uid: uuid.UUID, session: AsyncSession) -> Sequence[Appointment]:

    stmt = select(Appointment).where(Appointment.status != AppointmentStatus.COMPLETED, Appointment.hospital_uid == hospital_uid).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    ).order_by(Appointment.scheduled_time) #type: ignore

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_single_practitioner(practitioner_uid: uuid.UUID, session: AsyncSession) -> Practitioner | Any:

    stmt = select(Practitioner).where(Practitioner.uid == practitioner_uid).options(
        selectinload(Practitioner.user),
        selectinload(Practitioner.hospital).selectinload(Hospital.user),
        selectinload(Practitioner.department)
    )

    result = await session.execute(stmt)

    return result.scalar_one_or_none()



async def cancel_appointment(appointment_uid: uuid.UUID, session: AsyncSession):
    
    appointment = await get_appointment_by_id(appointment_uid, session)
    
    if not appointment:
        return None
    
    appointment.status = AppointmentStatus.CANCELED
    await session.commit()
    await session.refresh(appointment)

    return appointment


async def get_all_pending_appointments(session: AsyncSession) -> Sequence[Appointment]:
    
    stmt = select(Appointment).where(Appointment.status == AppointmentStatus.PENDING).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    ).order_by(Appointment.scheduled_time) #type: ignore

    result = await session.execute(stmt)

    return result.scalars().all()



async def get_patient_pending_appointments(patient_uid: uuid.UUID, session: AsyncSession) -> Appointment | None:

    stmt = select(Appointment).where(Appointment.patient_uid == patient_uid, Appointment.status != AppointmentStatus.COMPLETED).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.practitioner).selectinload(Practitioner.user),
        selectinload(Appointment.hospital).selectinload(Hospital.user),
        selectinload(Appointment.department)
    )
    
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def switch_appointment_status(appointment_uid: uuid.UUID, new_status: AppointmentStatusUpdate, session: AsyncSession) -> Appointment | None:

    appointment = await get_appointment_by_id(appointment_uid, session)
    
    if not appointment:
        return None
    
    appointment.status = new_status.status

    await session.commit()
    await session.refresh(appointment)

    return appointment


async def delete_appointment(appointment_uid: uuid.UUID, session: AsyncSession):

    appointment = await get_appointment_by_id(appointment_uid, session)
    
    if not appointment:
        return None
    
    await session.delete(appointment)
    await session.commit()

    await notify_queue_update(session, appointment.hospital_uid)


async def reschedule_appointment(
    appointment_uid: uuid.UUID,
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
        old_time=old_time, #type: ignore
        new_time=payload.new_time,
        reason=payload.reason,
        rescheduled_by=current_user.uid,
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



async def mark_missed_appointments(
    session: AsyncSession,
) -> int:

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)

    stmt = (
        update(Appointment)
        .where(
            Appointment.scheduled_time < cutoff, #type: ignore
            Appointment.status.in_( #type: ignore
                [
                    AppointmentStatus.PENDING,
                    AppointmentStatus.IN_PROGRESS,
                    AppointmentStatus.RESCHEDULED
                ]
            ),
        )
        .values(
            status=AppointmentStatus.MISSED
        )
    )

    result = await session.execute(stmt)

    await session.commit()

    return result.rowcount or 0