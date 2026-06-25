import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.core.dependencies import get_current_user
from src.app import schemas, models
from src.app.services import statistics as stats_service, hospital as hp_service
from src.app.core import errors
from src.app.database.main import get_session

stats_router = APIRouter(
    tags=['Statistics']
)

# Hospital Statistics Endpoints

@stats_router.get('/hospitals/appointment-stats', status_code=status.HTTP_200_OK, response_model=schemas.HospitalAppointmentStats)
async def get_hospital_appointment_stats(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get core appointment statistics for a hospital"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    stats = await stats_service.get_hospital_appointment_stats(hospital_uid, session)
    return stats


@stats_router.get('/hospitals/time-based-stats', status_code=status.HTTP_200_OK)
async def get_hospital_time_based_stats(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get time-based appointment statistics for a hospital"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    stats = await stats_service.get_hospital_time_based_stats(hospital_uid, session)
    return stats


@stats_router.get('/hospitals/average-appointments-per-day', status_code=status.HTTP_200_OK)
async def get_hospital_average_appointments_per_day(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get average appointments per day for a hospital"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    avg = await stats_service.get_hospital_average_appointments_per_day(hospital_uid, session)
    return {"average_appointments_per_day": avg}


@stats_router.get('/hospitals/rescheduled-appointments', status_code=status.HTTP_200_OK)
async def get_hospital_rescheduled_appointments(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get count of rescheduled appointments for a hospital"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    count = await stats_service.get_hospital_rescheduled_appointments(hospital_uid, session)
    return {"rescheduled_appointments": count}


@stats_router.get('/hospitals/average-wait-time', status_code=status.HTTP_200_OK)
async def get_hospital_average_wait_time(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get average wait time in hours for a hospital"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    avg_wait = await stats_service.get_hospital_average_wait_time(hospital_uid, session)
    return {"average_wait_time_hours": avg_wait}


@stats_router.get('/hospitals/cancellation-rate', status_code=status.HTTP_200_OK)
async def get_hospital_cancellation_rate(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get cancellation rate percentage for a hospital"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    rate = await stats_service.get_hospital_cancellation_rate(hospital_uid, session)
    return {"cancellation_rate_percent": rate}


@stats_router.get('/hospitals/appointments-by-department', status_code=status.HTTP_200_OK)
async def get_appointments_by_department(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get appointment counts grouped by department"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    data = await stats_service.get_appointments_by_department(hospital_uid, session)
    return {"appointments_by_department": data}


@stats_router.get('/hospitals/appointments-by-practitioner', status_code=status.HTTP_200_OK)
async def get_appointments_by_practitioner(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get appointment counts grouped by practitioner"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    data = await stats_service.get_appointments_by_practitioner(hospital_uid, session)
    return {"appointments_by_practitioner": data}


@stats_router.get('/hospitals/top-departments', status_code=status.HTTP_200_OK)
async def get_top_departments_by_appointments(hospital_uid: uuid.UUID, limit: int = 5, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get top departments by appointment volume"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    data = await stats_service.get_top_departments_by_appointments(hospital_uid, session, limit)
    return {"top_departments": data}


@stats_router.get('/hospitals/top-practitioners', status_code=status.HTTP_200_OK)
async def get_top_practitioners_by_appointments(hospital_uid: uuid.UUID, limit: int = 5, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get top practitioners by appointment volume"""
    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()

    data = await stats_service.get_top_practitioners_by_appointments(hospital_uid, session, limit)
    return {"top_practitioners": data}


# Patient Statistics Endpoints

@stats_router.get('/patients/appointment-stats', status_code=status.HTTP_200_OK)
async def get_patient_appointment_stats(session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    """Get appointment statistics for the current patient"""
    if current_user.role != models.UserRoles.PATIENT:
        raise errors.NotAuthorized()
    
    from sqlmodel import select
    patient_stmt = select(models.Patient).where(models.Patient.user_uid == current_user.uid)
    result = await session.execute(patient_stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise errors.PatientNotFound()
    
    total = await stats_service.get_patient_total_appointments(str(patient.uid), session)
    upcoming = await stats_service.get_patient_upcoming_appointments(str(patient.uid), session)
    completed = await stats_service.get_patient_completed_appointments(str(patient.uid), session)

    return {
        "total_appointments": total,
        "upcoming_appointments": upcoming,
        "completed_appointments": completed
    }