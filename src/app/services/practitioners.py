from typing import Optional
import uuid
from sqlalchemy import func, or_, desc, asc
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from src.app.models import PractitionerStatus, Hospital, PractitionerType, Practitioner
from src.app.schemas import PractitionerProfileUpdate


async def search_practitioner(
    session: AsyncSession,
    q: Optional[str] = None,
    specialization: Optional[str] = None,
    hospital_id: Optional[str] = None,
    is_available: Optional[bool] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "last_name",
    sort_dir: str = "asc",
) -> dict:
    stmt = select(Practitioner).options(
        selectinload(Practitioner.user),
        selectinload(Practitioner.hospital).selectinload(Hospital.user),
        selectinload(Practitioner.department)
    )

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Practitioner.last_name.ilike(pattern), # type: ignore
                Practitioner.specialization.ilike(pattern), #type: ignore
                Practitioner.bio.ilike(pattern), #type: ignore
            )
        )

    if specialization:
        stmt = stmt.where(Practitioner.specialization == specialization)
    if hospital_id:
        stmt = stmt.where(Practitioner.hospital_uid == hospital_id)
    if is_available is not None:
        stmt = stmt.where(Practitioner.is_available == is_available)
    if status:
        stmt = stmt.where(Practitioner.status == status)

    order_col = getattr(Practitioner, sort_by, Practitioner.last_name)
    stmt = stmt.order_by(asc(order_col) if sort_dir ==
                         "asc" else desc(order_col))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(stmt)
    practitioners = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [Practitioner.model_validate(d) for d in practitioners]
    }


async def get_all_practitioners(skip: int, limit: int, practitioner_type: PractitionerType | None, session: AsyncSession):

   stmt = select(Practitioner).offset(skip).limit(limit).options(
       selectinload(Practitioner.user),
       selectinload(Practitioner.hospital).selectinload(Hospital.user),
       selectinload(Practitioner.department)
   )

   if practitioner_type:
       filtered = stmt.where(Practitioner.practitioner_type == practitioner_type)
   
   result = await session.execute(filtered)

   return result.scalars().all()


async def get_pending_practitioners(hospital_id: uuid.UUID, type: PractitionerType | None, skip: int, limit: int, session: AsyncSession):
    
    stmt = select(Practitioner).where(Practitioner.hospital_uid == hospital_id, 
                                Practitioner.status == PractitionerStatus.UNDER_REVIEW).offset(skip).limit(limit).options(
       selectinload(Practitioner.user),
       selectinload(Practitioner.hospital).selectinload(Hospital.user),
       selectinload(Practitioner.department)
   )
    
    if type:
        stmt = stmt.where(Practitioner.practitioner_type == type)
    
    result = await session.execute(stmt)

    return result.scalars().all()

async def get_practitioner(practitioner_id: uuid.UUID, session: AsyncSession):

   stmt = select(Practitioner).where(Practitioner.uid == practitioner_id).options(
       selectinload(Practitioner.user),
       selectinload(Practitioner.hospital).selectinload(Hospital.user),
       selectinload(Practitioner.department)
   )
   result = await session.execute(stmt)

   return result.scalar_one_or_none()


async def change_practitioner_availability(practitioner_id: uuid.UUID, session: AsyncSession):

   practitioner = await get_practitioner(practitioner_id=practitioner_id, session=session)

   if practitioner is not None:
      practitioner.is_available = not practitioner.is_available

      await session.commit()
      await session.refresh(practitioner)
   
   return practitioner
   


async def approve_practitioner(practitioner_id: uuid.UUID, session: AsyncSession, status: PractitionerStatus):
   practitioner_to_approve = await get_practitioner(practitioner_id=practitioner_id, session=session)

   if practitioner_to_approve is not None:
      practitioner_to_approve.status = status

      await session.commit()
      await session.refresh(practitioner_to_approve)

      return practitioner_to_approve
   else:
      return None
   
       
async def update_practitioner_info(practitioner_id: uuid.UUID, update_data: PractitionerProfileUpdate, session: AsyncSession):
    practitioner_to_update = await get_practitioner(practitioner_id=practitioner_id, session=session)

    if practitioner_to_update is not None:
        update_data_dict = update_data.model_dump(
            exclude_unset=True)

        for k, v in update_data_dict.items():
            setattr(practitioner_to_update, k, v)

        await session.commit()
        await session.refresh(practitioner_to_update)

        return practitioner_to_update
    return None


async def delete_practitioner(practitioner_id: uuid.UUID, session: AsyncSession):
    
    practitioner = await get_practitioner(practitioner_id=practitioner_id, session=session)

    if practitioner is not None:

        await session.delete(practitioner)

        await session.commit()

        return {}

    else:
        return None
