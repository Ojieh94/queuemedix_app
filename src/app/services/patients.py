from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, or_
from src.app.models import Patient, User
from typing import Optional
from src.app.schemas import PatientProfileUpdate


async def get_patient(patient_uid: str, session: AsyncSession):
    
    stmt = select(Patient).where(Patient.uid == patient_uid).options(selectinload(Patient.user))

    result = await session.execute(stmt)

    return result.scalar_one_or_none()

async def get_patient_by_user_uid(user_uid: str, session: AsyncSession) -> Patient | None:
    
    stmt = select(Patient).where(Patient.user_uid == user_uid)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()



async def update_patient(payload: PatientProfileUpdate, patient_uid: str, session: AsyncSession):
    
    patient_to_update = await get_patient(patient_uid, session)

    if patient_to_update is not None:

        patient_dict = payload.model_dump(exclude_unset=True)

        for k, v in patient_dict.items():
            setattr(patient_to_update, k, v)
        
        await session.commit()
        await session.refresh(patient_to_update)
        
        return patient_to_update
    
    else:
        return None
    


async def get_all_patients(skip: int, limit: int, search: Optional[str], session: AsyncSession):

    stmt = select(Patient).offset(skip).limit(limit).options(selectinload(Patient.user))

    if search:
        stmt = stmt.filter(or_(Patient.first_name.contains(search), Patient.last_name.contains(search), Patient.hospital_card_id.contains(search)))

    result = await session.execute(stmt)

    return result.scalars()


async def get_patient_by_card(card_id: str, session: AsyncSession):

    stmt = select(Patient).where(Patient.hospital_card_id == card_id).options(selectinload(Patient.user))

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def delete_patient(patient_uid: int, session: AsyncSession):

    patient_to_delete = await get_patient(patient_uid, session)

    if patient_to_delete is not None:

        await session.delete(patient_to_delete)

        await session.commit()
    
    else:
        return None