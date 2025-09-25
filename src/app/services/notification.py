from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import Notification
from src.app.websocket.connection_manager import manager


async def send_notification(session: AsyncSession, user_uid: str, payload: dict):
    """
    Store a notification in DB and broadcast in real-time.
    """
    notif = Notification(
        user_uid=user_uid,
        title=payload.get("title", "Notification"),
        body=payload.get("body", ""),
        data=payload.get("data", {})
    )
    session.add(notif)
    await session.commit()
    await session.refresh(notif)

    # Push via websocket (channel = notifications, room = user_uid)
    await manager.broadcast("notifications", str(user_uid), {
        "uid": str(notif.uid),
        "title": notif.title,
        "body": notif.body,
        "data": notif.data,
        "timestamp": notif.timestamp.isoformat()
    })

    return notif
