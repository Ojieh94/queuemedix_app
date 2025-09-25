from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.app.websocket.connection_manager import manager

router = APIRouter(prefix="/ws", tags=["Notifications", "Websockets"])


@router.websocket("/ws/notifications/{user_uid}")
async def notifications_ws(websocket: WebSocket, user_uid: str):

    """Notification websocket connection (DM and general application of notifications)"""

    await manager.connect(websocket, "notifications", user_uid)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "notifications", user_uid)


