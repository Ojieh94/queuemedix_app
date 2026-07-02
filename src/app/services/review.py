import uuid

from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.orm import selectinload
from src.app.models import AppointmentStatus, Hospital, Patient, Practitioner, User, Review
from src.app.schemas import ReviewCreate
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.core import errors
from src.app.services import appointment as appt_service, hospital as hp_service, practitioners as pract_service
from src.app.services.review_calculator import calculate_average

async def create_review(
    review_data: ReviewCreate,
    current_user: User,
    session: AsyncSession,
):
    """
    Create a review for a completed appointment.
    """

    if not current_user.patient:
        raise errors.NotAuthorized()

    appointment = await appt_service.get_appointment_by_id(
        review_data.appointment_uid,
        session,
    )

    if not appointment:
        raise errors.AppointmentNotFound()

    if appointment.patient_uid != current_user.patient.uid:
        raise errors.NotAuthorized()

    if appointment.status != AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You can not review an uncompleted appointment"
        )

    existing_review = await get_review_by_appointment(
        review_data.appointment_uid,
        session,
    )

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="You've already reviewed this appointment."
        )

    hospital = await hp_service.get_single_hospital(
        appointment.hospital_uid,
        session,
    )

    practitioner = await pract_service.get_practitioner(
        appointment.practitioner_uid,
        session,
    )

    review = Review(
        appointment_uid=appointment.uid,
        patient_uid=current_user.patient.uid,
        hospital_uid=appointment.hospital_uid,
        practitioner_uid=appointment.practitioner_uid,
        hospital_rating=review_data.hospital_rating,
        practitioner_rating=review_data.practitioner_rating,
        comment=review_data.comment,
    )

    session.add(review)

    # Update hospital rating
    hospital.average_rating, hospital.rating_count = calculate_average(
        hospital.average_rating,
        hospital.rating_count,
        review_data.hospital_rating,
    )

    #Upate practitioner rating
    practitioner.average_rating, practitioner.rating_count = calculate_average(
        practitioner.average_rating,
        practitioner.rating_count,
        review_data.practitioner_rating,
    )

    await session.commit()
    await session.refresh(review)

    return review

async def get_review_by_appointment(appointment_uid, session:AsyncSession):

    stmt = select(Review).where(Review.appointment_uid == appointment_uid)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()

async def get_hospital_reviews(
    hospital_uid: uuid.UUID,
    offset: int,
    limit: int,
    session: AsyncSession,
):
    stmt = (
        select(Review)
        .where(Review.hospital_uid == hospital_uid)
        .options(
            selectinload(Review.patient).selectinload(Patient.user),
            selectinload(Review.practitioner).selectinload(Practitioner.user),
        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(stmt)

    return result.scalars().all()

async def get_practitioner_reviews(
    practitioner_uid: uuid.UUID,
    offset: int,
    limit: int,
    session: AsyncSession,
):
    stmt = (
        select(Review)
        .where(Review.practitioner_uid == practitioner_uid)
        .options(
            selectinload(Review.hospital).selectinload(Hospital.user),
            selectinload(Review.patient).selectinload(Patient.user),
        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(stmt)

    return result.scalars().all()

async def get_patient_reviews(
    patient_uid: uuid.UUID,
    offset: int,
    limit: int,
    session: AsyncSession,
):
    stmt = (
        select(Review)
        .where(Review.patient_uid == patient_uid)
        .options(
            selectinload(Review.hospital).selectinload(Hospital.user),
            selectinload(Review.practitioner).selectinload(Practitioner.user),
        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(stmt)

    return result.scalars().all()