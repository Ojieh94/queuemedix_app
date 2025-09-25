from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc

from src.app.websocket.connection_manager import manager
from src.app.models import Appointment
from src.app.core.dependencies import get_session
from src.app.core.utils import remaining_time

router = APIRouter(prefix="/ws", tags=["Appointments", "Websockets"])


@router.websocket("/appointments/{hospital_uid}")
async def appointments_ws(websocket: WebSocket, hospital_uid: str, session: AsyncSession = Depends(get_session)):
    """
    WebSocket endpoint that streams appointment queue updates filtered by hospital.
    """
    await manager.connect(websocket, "appointments", hospital_uid)

    try:
        # Send initial queue data when a client connects
        await send_initial_queue(websocket, session, hospital_uid)

        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "appointments", hospital_uid)


async def notify_queue_update(session: AsyncSession, hospital_uid: str):
    """
    Sends updated queue only to clients connected to the specific hospital.
    """
    queue = (
        await session.execute(
            select(Appointment)
            .where(Appointment.hospital_uid == hospital_uid)
            .order_by(asc(Appointment.scheduled_time))
        )
    ).scalars().all()

    queue_data = [
        {
            "id": appt.uid,
            "patient": appt.patient.full_name,
            "patient_id": appt.patient_uid,
            "time": appt.scheduled_time.isoformat(),
            "status": appt.status.value,
            "appointment_due": remaining_time(appt.scheduled_time),
        }
        for appt in queue
    ]

    await manager.broadcast("appointments", hospital_uid, {
        "type": "queue_update",
        "data": queue_data
    })


async def send_initial_queue(websocket: WebSocket, session: AsyncSession, hospital_uid: str):
    """
    Sends the current queue to a newly connected WebSocket client for a specific hospital.
    """
    queue = (
        await session.execute(
            select(Appointment)
            .where(Appointment.hospital_uid == hospital_uid)
            .order_by(asc(Appointment.scheduled_time))
        )
    ).scalars().all()

    queue_data = [
        {
            "id": appt.uid,
            "patient": appt.patient.full_name,
            "patient_id": appt.patient_uid,
            "time": appt.scheduled_time.isoformat(),
            "status": appt.status.value,
            "appointment_due": remaining_time(appt.scheduled_time),
        }
        for appt in queue
    ]

    await websocket.send_json({
        "type": "queue_update",
        "data": queue_data
    })
