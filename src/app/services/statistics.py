from sqlalchemy import func, and_, or_, case, extract
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models import Appointment, AppointmentStatus, Department, Doctor
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from src.app.schemas import HospitalAppointmentStats


async def get_hospital_appointment_stats(hospital_uid: str, session: AsyncSession) -> HospitalAppointmentStats:
    """Get core appointment statistics for a hospital"""
    today = date.today()

    # Total appointments
    total_stmt = select(func.count(Appointment.uid)).where(Appointment.hospital_uid == hospital_uid)
    total_result = await session.execute(total_stmt)
    total_appointments = total_result.scalar_one()

    # Today's appointments
    todays_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.scheduled_time.isnot(None),
        func.date(Appointment.scheduled_time) == today
    )
    todays_result = await session.execute(todays_stmt)
    todays_appointments = todays_result.scalar_one()

    # Pending appointments
    pending_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.PENDING
    )
    pending_result = await session.execute(pending_stmt)
    pending_appointments = pending_result.scalar_one()

    # Completed appointments
    completed_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.COMPLETED
    )
    completed_result = await session.execute(completed_stmt)
    completed_appointments = completed_result.scalar_one()

    # Canceled appointments
    canceled_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.CANCELED
    )
    canceled_result = await session.execute(canceled_stmt)
    canceled_appointments = canceled_result.scalar_one()

    # In-progress appointments
    in_progress_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.IN_PROGRESS
    )
    in_progress_result = await session.execute(in_progress_stmt)
    in_progress_appointments = in_progress_result.scalar_one()

    return HospitalAppointmentStats(
        total_appointments=total_appointments,
        todays_appointments=todays_appointments,
        pending_appointments=pending_appointments,
        completed_appointments=completed_appointments,
        canceled_appointments=canceled_appointments,
        in_progress_appointments=in_progress_appointments,
    )


async def get_hospital_time_based_stats(hospital_uid: str, session: AsyncSession) -> Dict[str, int]:
    """Get time-based appointment statistics"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_week = today + timedelta(days=7)

    # This week's appointments
    week_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.scheduled_time.isnot(None),
        func.date(Appointment.scheduled_time).between(week_start, week_end)
    )
    week_result = await session.execute(week_stmt)
    this_week_appointments = week_result.scalar_one()

    # This month's appointments
    month_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.scheduled_time.isnot(None),
        extract('year', Appointment.scheduled_time) == today.year,
        extract('month', Appointment.scheduled_time) == today.month
    )
    month_result = await session.execute(month_stmt)
    this_month_appointments = month_result.scalar_one()

    # Upcoming appointments (next 7 days)
    upcoming_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.scheduled_time.isnot(None),
        func.date(Appointment.scheduled_time) > today,
        func.date(Appointment.scheduled_time) <= next_week
    )
    upcoming_result = await session.execute(upcoming_stmt)
    upcoming_appointments = upcoming_result.scalar_one()

    return {
        "this_week_appointments": this_week_appointments,
        "this_month_appointments": this_month_appointments,
        "upcoming_appointments": upcoming_appointments,
    }


async def get_hospital_average_appointments_per_day(hospital_uid: str, session: AsyncSession) -> float:
    """Calculate average appointments per day over the last 30 days"""
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # Count appointments in last 30 days
    count_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.scheduled_time.isnot(None),
        func.date(Appointment.scheduled_time) >= thirty_days_ago
    )
    count_result = await session.execute(count_stmt)
    total_in_period = count_result.scalar_one()

    # Average per day
    if total_in_period > 0:
        return round(total_in_period / 30, 2)
    return 0.0


async def get_hospital_rescheduled_appointments(hospital_uid: str, session: AsyncSession) -> int:
    """Get count of rescheduled appointments"""
    stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.RESCHEDULED
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_hospital_average_wait_time(hospital_uid: str, session: AsyncSession) -> float:
    """Calculate average wait time in hours for completed appointments"""
    stmt = select(
        func.avg(
            func.extract('epoch', Appointment.completed_time - Appointment.check_in_time) / 3600
        )
    ).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.check_in_time.isnot(None),
        Appointment.completed_time.isnot(None)
    )
    result = await session.execute(stmt)
    avg_wait = result.scalar_one()
    return round(avg_wait, 2) if avg_wait else 0.0


async def get_hospital_cancellation_rate(hospital_uid: str, session: AsyncSession) -> float:
    """Calculate cancellation rate as percentage"""
    total_stmt = select(func.count(Appointment.uid)).where(Appointment.hospital_uid == hospital_uid)
    total_result = await session.execute(total_stmt)
    total = total_result.scalar_one()

    if total == 0:
        return 0.0

    canceled_stmt = select(func.count(Appointment.uid)).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.status == AppointmentStatus.CANCELED
    )
    canceled_result = await session.execute(canceled_stmt)
    canceled = canceled_result.scalar_one()

    return round((canceled / total) * 100, 2)


async def get_appointments_by_department(hospital_uid: str, session: AsyncSession) -> List[Dict[str, Any]]:
    """Get appointment counts grouped by department"""
    stmt = select(
        Department.name,
        func.count(Appointment.uid).label('count')
    ).join(
        Appointment, Department.uid == Appointment.department_uid
    ).where(
        Appointment.hospital_uid == hospital_uid
    ).group_by(
        Department.uid, Department.name
    ).order_by(
        func.count(Appointment.uid).desc()
    )

    result = await session.execute(stmt)
    return [{"department": row.name, "count": row.count} for row in result]


async def get_appointments_by_doctor(hospital_uid: str, session: AsyncSession) -> List[Dict[str, Any]]:
    """Get appointment counts grouped by doctor"""
    stmt = select(
        Doctor.full_name,
        func.count(Appointment.uid).label('count')
    ).join(
        Appointment, Doctor.uid == Appointment.doctor_uid
    ).where(
        Appointment.hospital_uid == hospital_uid,
        Appointment.doctor_uid.isnot(None)
    ).group_by(
        Doctor.uid, Doctor.full_name
    ).order_by(
        func.count(Appointment.uid).desc()
    )

    result = await session.execute(stmt)
    return [{"doctor": row.full_name, "count": row.count} for row in result]


async def get_top_departments_by_appointments(hospital_uid: str, session: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    """Get top departments by appointment volume"""
    data = await get_appointments_by_department(hospital_uid, session)
    return data[:limit]


async def get_top_doctors_by_appointments(hospital_uid: str, session: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    """Get top doctors by appointment volume"""
    data = await get_appointments_by_doctor(hospital_uid, session)
    return data[:limit]


async def get_patient_total_appointments(patient_uid: str, session: AsyncSession) -> int:
    """Get total appointments for a patient"""
    stmt = select(func.count(Appointment.uid)).where(Appointment.patient_uid == patient_uid)
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_patient_upcoming_appointments(patient_uid: str, session: AsyncSession) -> int:
    """Get upcoming appointments for a patient"""
    today = date.today()
    stmt = select(func.count(Appointment.uid)).where(
        Appointment.patient_uid == patient_uid,
        Appointment.scheduled_time.isnot(None),
        func.date(Appointment.scheduled_time) >= today
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_patient_completed_appointments(patient_uid: str, session: AsyncSession) -> int:
    """Get completed appointments for a patient"""
    stmt = select(func.count(Appointment.uid)).where(
        Appointment.patient_uid == patient_uid,
        Appointment.status == AppointmentStatus.COMPLETED
    )
    result = await session.execute(stmt)
    return result.scalar_one()