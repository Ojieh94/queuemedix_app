from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_
from src.app.models import Hospital, Doctor, Appointment, AppointmentStatus, HospitalStatus, HospitalRating
from typing import Optional, List
from src.app.schemas import HospitalProfileUpdate, VerifyHospital, AssignAdminDuty
from src.app.services import admins as ad_service


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
async def get_hospitals(skip: int, limit: int, session: AsyncSession, search: Optional[str] = None, location: Optional[str] = None):

    stmt = select(Hospital).offset(skip).limit(limit)

    if search:
        stmt = stmt.filter(or_(
            Hospital.hospital_name.contains(search),
            Hospital.full_address.contains(search),
            Hospital.state.contains(search)
        ))

    if location:
        stmt = stmt.filter(or_(
            Hospital.full_address.contains(location),
            Hospital.state.contains(location)
        ))

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


async def get_hospital_rating(hospital_uid: str, user_uid: str, session: AsyncSession):
    stmt = select(HospitalRating).where(
        HospitalRating.hospital_uid == hospital_uid,
        HospitalRating.user_uid == user_uid
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def compute_hospital_average_rating(hospital_uid: str, session: AsyncSession) -> float:
    stmt = select(func.avg(HospitalRating.rating)).where(
        HospitalRating.hospital_uid == hospital_uid
    )
    result = await session.execute(stmt)
    average = result.scalar_one_or_none() or 0.0
    return float(round(average, 1))


async def rate_hospital(hospital_uid: str, user_uid: str, rating_value: float, session: AsyncSession):
    hospital = await get_single_hospital(hospital_uid, session)

    if not hospital:
        return None

    rating_value = float(round(Decimal(str(rating_value)), 1))

    existing_rating = await get_hospital_rating(hospital_uid, user_uid, session)
    if existing_rating:
        existing_rating.rating = rating_value
    else:
        rating_record = HospitalRating(
            hospital_uid=hospital_uid,
            user_uid=user_uid,
            rating=rating_value
        )
        session.add(rating_record)

    await session.commit()

    hospital.average_rating = await compute_hospital_average_rating(hospital_uid, session)
    await session.commit()
    await session.refresh(hospital)

    return hospital


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


async def approve_hospital(hospital_uid: str, payload: VerifyHospital, session: AsyncSession):
        
        hospital = await get_single_hospital(hospital_uid, session)

        if not hospital:
            return None
        
        hospital.status = payload.status

        if payload.status == HospitalStatus.APPROVED:
            hospital.is_verified = True

        await session.commit()
        
        return hospital


async def assign_duties_to_department_admin(admin_uid: str, payload: AssignAdminDuty, session: AsyncSession):
    
    admin = await ad_service.get_admin(admin_uid, session)
    
    if not admin:
        return None
    
    admin.notes = payload.notes

    await session.commit()
    
    return admin
    
