from datetime import datetime
from typing import List, Optional
from collections.abc import Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from src.app.models import MedicalRecord, Patient, Practitioner, Hospital, MedicalRecordFile
from src.app.schemas import MedicalRecordCreate, MedicalRecordUpdate






async def create_medical_record(payload: MedicalRecordCreate, session: AsyncSession):
    """Create a new medical record in the database."""

    new_record = MedicalRecord(**payload.model_dump())
    session.add(new_record)
    
    await session.commit()
    await session.refresh(new_record)

    return new_record

    
async def get_medical_record_by_id(record_id: uuid.UUID, session: AsyncSession) -> Optional[MedicalRecord]:
    """Retrieve a medical record by its unique identifier."""
    stmt = select(MedicalRecord).where(MedicalRecord.uid == record_id).options(
        selectinload(MedicalRecord.patient).selectinload(Patient.user),
        selectinload(MedicalRecord.practitioner).selectinload(Practitioner.user),
        selectinload(MedicalRecord.hospital).selectinload(Hospital.user)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_medical_record_by_patient(patient_id: uuid.UUID, hospital_id: uuid.UUID | None, offset: int, limit: int, session: AsyncSession) -> Sequence[MedicalRecord]:
    """Retrieve medical records for a specific patient in a hospital with pagination."""
    stmt = select(MedicalRecord).where(
        MedicalRecord.patient_uid == patient_id,
        ).options(
        selectinload(MedicalRecord.patient).selectinload(Patient.user),
        selectinload(MedicalRecord.practitioner).selectinload(Practitioner.user),
        selectinload(MedicalRecord.hospital).selectinload(Hospital.user),
        selectinload(MedicalRecord.files).selectinload(MedicalRecordFile.medical_record)
    ).offset(offset).limit(limit)
    
    if hospital_id is not None:
        stmt = stmt.where(MedicalRecord.hospital_uid == hospital_id
    )

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_hospital_medical_records(hospital_id: uuid.UUID, offset: int, limit: int, session: AsyncSession) -> Sequence[MedicalRecord]:
    """Retrieve all medical records for a specific hospital."""
    stmt = select(MedicalRecord).where(MedicalRecord.hospital_uid == hospital_id).options(
        selectinload(MedicalRecord.patient).selectinload(Patient.user),
        selectinload(MedicalRecord.practitioner_uid).selectinload(Practitioner.user),
        selectinload(MedicalRecord.hospital).selectinload(Hospital.user)
    ).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def search_medical_records_by_hospital(
    session: AsyncSession,
    hospital_uid: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    patient_uid: Optional[uuid.UUID] = None,
    practitioner_uid: Optional[uuid.UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Sequence[MedicalRecord]:
    query = select(MedicalRecord).where(
        MedicalRecord.hospital_uid == hospital_uid)

    if patient_uid:
        query = query.where(MedicalRecord.patient_uid == patient_uid)
    if practitioner_uid:
        query = query.where(MedicalRecord.practitioner.uid == practitioner_uid)
    if date_from and date_to:
        query = query.where(
            MedicalRecord.created_at.between(date_from, date_to)) #type: ignore

    result = await session.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    return result.scalars().all()


async def update_patient_medical_record(record_id: uuid.UUID, payload: MedicalRecordUpdate, session: AsyncSession) -> Optional[MedicalRecord]:
    """Update an existing medical record with new data."""
    record_to_update = await get_medical_record_by_id(record_id=record_id, session=session)

    if record_to_update is not None:
        record_dict = payload.model_dump(exclude_unset=True)

        for k, v in record_dict.items():
            setattr(record_to_update, k, v)

        await session.commit()
        await session.refresh(record_to_update)

        return record_to_update

    else:
        return None
    


async def delete_medical_record(record_id: uuid.UUID, session: AsyncSession) -> bool:
    """Delete a medical record by its unique identifier."""
    record = await get_medical_record_by_id(record_id=record_id, session=session)

    if record is not None:
        await session.delete(record)
        await session.commit()
        return True
    else:
        return False


