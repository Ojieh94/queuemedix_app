import uuid

from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, timezone

from src.app.models import Appointment, QueueEntry, AppointmentStatus, Queue, QueueEntryStatus


async def create_queue_entry(
    appointment: Appointment, session: AsyncSession
) -> QueueEntry | dict:

    # Validate appointment
    if not appointment.practitioner_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor has not been assigned to this appointment.",
        )

    if appointment.status in (
        AppointmentStatus.CANCELED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.MISSED,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Appointment is not eligible for queue entry.",
        )

    # Check if queue entry already exists
    existing_entry = await get_queue_by_appointment_uid(
        session=session,
        appointment_uid=appointment.uid,
    )

    if existing_entry:
        return existing_entry

    # Find queue
    queue = await get_queue(
        session=session,
        hospital_uid=appointment.hospital_uid,
    )

    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No queue found for the hospital.")

    # Generate queue number
    queue_number = await get_next_queue_number(
        session=session,
        queue_uid=queue.uid,
    )

    # Create queue entry
    queue_entry = QueueEntry(
        queue_uid=queue.uid,
        appointment_uid=appointment.uid,
        patient_uid=appointment.patient_uid,
        queue_number=queue_number,
        status=QueueEntryStatus.WAITING,
        joined_at=datetime.now(timezone.utc),
    )

    # Save queue entry
    session.add(queue_entry)
    await session.commit()
    await session.refresh(queue_entry)

    return {"message": "Queue entered successfully."}


async def get_queue_by_appointment_uid(
    session: AsyncSession, appointment_uid: uuid.UUID
) -> QueueEntry | None:

    statement = select(QueueEntry).where(QueueEntry.appointment_uid == appointment_uid)

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def get_queue(session: AsyncSession, hospital_uid: uuid.UUID) -> Queue | None:

    statement = select(Queue).where(Queue.hospital_uid == hospital_uid)

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def get_next_queue_number(queue_uid: uuid.UUID, session: AsyncSession) -> int:
    statement = select(func.max(QueueEntry.queue_number)).where(
        QueueEntry.queue_uid == queue_uid
    )

    result = await session.execute(statement)

    last_queue_number = result.scalar_one_or_none()

    return (last_queue_number or 0) + 1

async def get_active_queue_entry_by_patient_uid(session: AsyncSession, patient_uid: uuid.UUID) -> QueueEntry | None:

    statement = (select(QueueEntry) .where(
        QueueEntry.patient_uid == patient_uid,
        QueueEntry.status.in_( # type: ignore
            [
                QueueEntryStatus.WAITING,
                QueueEntryStatus.CALLED,
                QueueEntryStatus.SERVING,
            ]),
    ))

    result = await session.execute(statement)

    return result.scalar_one_or_none()

async def count_patients_ahead(session: AsyncSession, queue_uid: uuid.UUID, queue_number: int,) -> int:

    statement = select(
    func.count(QueueEntry.uid)).where(
    QueueEntry.queue_uid == queue_uid,
    QueueEntry.status == QueueEntryStatus.WAITING,
    QueueEntry.queue_number < queue_number)

    result = await session.execute(statement)

    return result.scalar_one()


async def get_queues(session: AsyncSession):
    stmt = select(Queue)

    result = await session.execute(stmt)

    return result.scalars()