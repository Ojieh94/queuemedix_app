import redis
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from src.app.websocket.connection_manager import manager
from src.app.core.settings import Config


router = APIRouter(prefix="/ws/support", tags=["Support", "Websockets"])

REDIS_URL = Config.REDIS_URL
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


@router.websocket("/{session_id}")
async def support_chat(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, "support", session_id)
    try:
        while True:
            data = await websocket.receive_json()

            # Save to Redis (short-lived)
            redis_client.rpush(f"support:{session_id}", str(data))

            # Broadcast message to both support + patient clients
            await manager.broadcast("support", session_id, data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, "support", session_id)
