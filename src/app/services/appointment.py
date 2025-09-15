from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List, Optional
from src.app.models import Appointment, AppointmentStatus, Doctor
from src.app.schemas import AppointmentCreate, AppointmentStatusUpdate
from src.app.router.queue_engine import notify_queue_update

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
    
    new_appointment = Appointment(**payload.model_dump(), patient_uid=patient_uid)

    session.add(new_appointment)
    await session.commit()
    await session.refresh(new_appointment)

    await notify_queue_update(hospital_uid=new_appointment.hospital_uid, session=session)

    return new_appointment 


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