from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import asc, select
from src.app.database.main import get_session
from app.models import Appointment
from src.app.core.utils import remaining_time

router = APIRouter(tags=['Appointment Queue'])


class ConnectionManager:
    def __init__(self):
        # Store active connections per hospital
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, hospital_uid: str):
        """ Accept WebSocket connection and associate it with a hospital ID """
        await websocket.accept()
        if hospital_uid not in self.active_connections:
            self.active_connections[hospital_uid] = []
        self.active_connections[hospital_uid].append(websocket)

    def disconnect(self, websocket: WebSocket, hospital_uid: str):
        """ Remove a disconnected WebSocket """
        if hospital_uid in self.active_connections:
            self.active_connections[hospital_uid].remove(websocket)
            # Remove empty hospital lists
            if not self.active_connections[hospital_uid]:
                del self.active_connections[hospital_uid]

    async def broadcast(self, hospital_uid: str, message: dict):
        """ Send a message to all clients connected to a specific hospital """
        if hospital_uid in self.active_connections:
            for connection in self.active_connections[hospital_uid]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{hospital_id}/appointment_queue")
async def websocket_endpoint(websocket: WebSocket, hospital_uid: str, session: AsyncSession = Depends(get_session)):

    """ WebSocket endpoint that streams appointment queue updates filtered by hospital """

    await manager.connect(websocket, hospital_uid)

    try:
        # Send initial queue data when a client connects
        await send_initial_queue(websocket, session, hospital_uid)

        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, hospital_uid)


async def notify_queue_update(session: AsyncSession, hospital_uid: str):

    """ Sends updated queue only to clients connected to the specific hospital """

    queue = (await session.execute(select(Appointment).where(Appointment.hospital_uid == hospital_uid).order_by(asc(Appointment.scheduled_time)))).scalars().all()

    queue_data = [{
        "id": appt.uid,
        "patient": appt.patient.full_name,
        "patient_id": appt.patient_uid,
        "time": appt.scheduled_time.isoformat(),
        "status": appt.status.value,
        "appointment_due": remaining_time(appt.scheduled_time)
    } for appt in queue]

    await manager.broadcast(hospital_uid, {"type": "queue_update", "data": queue_data})


async def send_initial_queue(websocket: WebSocket, session: AsyncSession, hospital_uid: str):

    """ Sends the current queue to a newly connected WebSocket client for a specific hospital """

    queue = (await session.execute(select(Appointment).where(Appointment.hospital_uid == hospital_uid).order_by(asc(Appointment.scheduled_time)))).scalars().all()

    queue_data = [{
        "id": appt.uid,
        "patient": appt.patient.full_name,
        "patient_id": appt.patient_uid,
        "time": appt.scheduled_time.isoformat(),
        "status": appt.status.value,
        "appointment_due": remaining_time(appt.scheduled_time)
    } for appt in queue]

    await websocket.send_json({"type": "queue_update", "data": queue_data})
