from typing import Optional
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models import Doctor, DoctorStatus
from src.app.schemas import DoctorProfileUpdate


async def search_doctors(
    session: AsyncSession,
    q: Optional[str] = None,
    specialization: Optional[str] = None,
    hospital_id: Optional[int] = None,
    is_available: Optional[bool] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "full_name",
    sort_dir: str = "asc",
) -> dict:
    stmt = select(Doctor)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Doctor.full_name.ilike(pattern),
                Doctor.specialization.ilike(pattern),
                Doctor.bio.ilike(pattern),
            )
        )

    if specialization:
        stmt = stmt.where(Doctor.specialization == specialization)
    if hospital_id:
        stmt = stmt.where(Doctor.hospital_uid == hospital_id)
    if is_available is not None:
        stmt = stmt.where(Doctor.is_available == is_available)
    if status:
        stmt = stmt.where(Doctor.status == status)

    order_col = getattr(Doctor, sort_by, Doctor.full_name)
    stmt = stmt.order_by(asc(order_col) if sort_dir ==
                         "asc" else desc(order_col))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(stmt)
    doctors = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [Doctor.model_validate(d) for d in doctors]
    }


async def get_all_doctors(skip: int, limit: int, session: AsyncSession):

   stmt = select(Doctor).offset(skip).limit(limit)
   result = await session.execute(stmt)

   return result.scalars().all()


async def get_pending_doctors(hospital_id: str, skip: int, limit: int, session: AsyncSession):
    
    stmt = select(Doctor).where(Doctor.hospital_uid == hospital_id, 
                                Doctor.status == DoctorStatus.UNDER_REVIEW).offset(skip).limit(limit)
    result = await session.execute(stmt)

    return result.scalars().all()

async def get_doctor(doctor_id: str, session: AsyncSession):

   stmt = select(Doctor).where(Doctor.uid == doctor_id)
   result = await session.execute(stmt)

   return result.scalar_one_or_none()


async def change_doctor_availability(doctor_id: str, session: AsyncSession):

   doctor = await get_doctor(doctor_id=doctor_id, session=session)

   if doctor is not None:
      doctor.is_available = not doctor.is_available
   
   return doctor
   


async def approve_doctor(doctor_id: str, session: AsyncSession, status: DoctorStatus):
   doctor_to_approve = await get_doctor(doctor_id=doctor_id, session=session)

   if doctor_to_approve is not None:
      doctor_to_approve.status = status

      await session.commit()

      return doctor_to_approve
   else:
      return None
   
       
async def update_doctor_info(doctor_id: str, update_data: DoctorProfileUpdate, session: AsyncSession):
    doctor_to_update = await get_doctor(doctor_id=doctor_id, session=session)

    if doctor_to_update is not None:
        update_data_dict = update_data.model_dump(
            exclude_unset=True)

        for k, v in update_data_dict.items():
            setattr(doctor_to_update, k, v)

        await session.commit()
        await session.refresh(doctor_to_update)

        return doctor_to_update
    return None


async def delete_doctor(doctor_id: str, session: AsyncSession):
    
    doctor = await get_doctor(doctor_id=doctor_id, session=session)

    if doctor is not None:

        await session.delete(doctor)

        await session.commit()

        return {}

    else:
        return None
