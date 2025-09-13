from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_
from src.app.models import Hospital, Doctor, Appointment, AppointmentStatus
from typing import Optional, List
from src.app.schemas import HospitalProfileUpdate


#updating hospital profile
async def update_hospital_profile(payload: HospitalProfileUpdate, hospital_uid: str, session: AsyncSession):
    
    hospital_to_update = await get_single_hospital(hospital_uid, session)

    if not hospital_to_update:
        return None
    
    hospital_dict = payload.model_dump(exclude_unset=True)

    for k, v in hospital_dict.items():
        setattr(hospital_to_update, k, v)
    
    await session.commit()
    await session.refresh(hospital_to_update)

    return hospital_to_update


#retrieving all hospitals
async def get_hospitals(skip: int, limit: int, search: Optional[str], session: AsyncSession):

    stmt = select(Hospital).offset(skip).limit(limit)

    if search is not None:
        stmt = stmt.filter(or_(Hospital.hospital_name.contains(search)))

    result = await session.execute(stmt)

    return result.scalars().all()


async def view_hospital_doctors(hospital_uid: str, availability: Optional[bool], session: AsyncSession):

    stmt = select(Doctor).where(Doctor.hospital_uid == hospital_uid)

    if availability is not None:
        stmt = stmt.where(Doctor.is_available == availability)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_single_hospital(hospital_uid: str, session: AsyncSession):

    stmt = select(Hospital).where(Hospital.uid == hospital_uid)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def view_hospital_appointments(hospital_uid: str, status: Optional[AppointmentStatus], session: AsyncSession) -> List[Appointment]:

    stmt = select(Appointment).where(Appointment.hospital_uid == hospital_uid)

    if status is not None:
        stmt = stmt.where(Appointment.status == status)

    result = await session.execute(stmt)

    return result.scalars().all()


async def delete_hospital(hospital_uid: str, session: AsyncSession):

    hospital_to_delete = await get_single_hospital(hospital_uid, session)

    if not hospital_to_delete:
        return None
    
    await session.delete(hospital_to_delete)

    await session.commit()
