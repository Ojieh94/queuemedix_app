from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession


from src.app.models import MedicalRecord
from src.app.schemas import  MedicalRecordCreate, MedicalRecordUpdate




async def create_medical_record(payload: MedicalRecordCreate, session: AsyncSession):
    
    medical_record = MedicalRecord(**payload.model_dump())
    session.add(medical_record)
    await session.commit()
    await session.refresh(medical_record)
    
    return medical_record

async def get_record(record_id: str, session: AsyncSession):
    stmt = select(MedicalRecord).where(MedicalRecord.uid == record_id)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()

async def get_patient_records(patient_id: str, hospital_id: str, skip: int, limit: int, session: AsyncSession):
    stmt = select(MedicalRecord).where(MedicalRecord.patient_uid == patient_id, MedicalRecord.hospital_uid == hospital_id).offset(skip).limit(limit)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_medical_records_by_hospital(
    session: AsyncSession,
    hospital_uid: str,
    page: int = 1,
    per_page: int = 20,
    patient_uid: Optional[str] = None,
    doctor_uid: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[MedicalRecord]:
    query = select(MedicalRecord).where(
        MedicalRecord.hospital_uid == hospital_uid)

    if patient_uid:
        query = query.where(MedicalRecord.patient_uid == patient_uid)
    if doctor_uid:
        query = query.where(MedicalRecord.doctor_uid == doctor_uid)
    if date_from and date_to:
        query = query.where(
            MedicalRecord.created_at.between(date_from, date_to))

    result = await session.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    return result.scalars().all()


async def update_medical_record(record_id: str, payload: MedicalRecordUpdate, session: AsyncSession):
    record_to_update = await get_record(record_id=record_id, session=session)

    if record_to_update is not None:

        record_dict = payload.model_dump(exclude_unset=True)

        for k, v in record_dict.items():
            setattr(record_to_update, k, v)

        await session.commit()
        await session.refresh(record_to_update)

        return record_to_update

    else:
        return None
