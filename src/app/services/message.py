from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models import Message, User
from src.app.schemas import MessageCreate, MessageUpdate
from src.app.websocket.connection_manager import manager
from src.app.services.notification import send_notification


async def send_message(payload: MessageCreate, current_user: User, session: AsyncSession):

    """
    Create a new message via REST.
    - sender = current_user (taken from JWT)
    - receiver = from payload
    - content = from payload
    """
    message = Message(
        sender_uid=current_user.uid,
        receiver_uid=payload.receiver_uid,
        content=payload.content
    )

    session.add(message)
    await session.commit()
    await session.refresh(message)

    # Build room_id consistently
    room_id = "_".join(sorted([str(message.sender_uid), str(message.receiver_uid)]))

    # Broadcast to subscribers of this DM room
    await manager.broadcast(
        channel="dm",
        room_id=room_id,
        message={
            "uid": str(message.uid),
            "sender_uid": str(message.sender_uid),
            "receiver_uid": str(message.receiver_uid),
            "content": message.content,
            "is_read": message.is_read,
            "timestamp": message.timestamp.isoformat()
        }
    )

    await send_notification(session, payload.receiver_uid, {
        "title": "New Message",
        "body": f"You have a new message from {current_user.username}",
        "data": {"message_uid": str(message.uid)}
    })

    return message


async def get_chat_history(other_user_id: str, session: AsyncSession, current_user: User,
):
   
    """Fetch chat history between the logged-in user and another user."""

    result = await session.execute(
        select(Message)
        .where(
            ((Message.sender_uid == current_user.uid) & (Message.receiver_uid == other_user_id)) |
            ((Message.sender_uid == other_user_id) & (Message.receiver_uid == current_user.uid))
        )
        .order_by(Message.timestamp)
    )

    return result.scalars().all()



async def get_message(message_uid: str, session: AsyncSession):

    stmt = select(Message).where(Message.uid == message_uid)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()



async def edit_message(message_uid: str, payload: MessageUpdate, session: AsyncSession):

    message = await get_message(message_uid, session)

    if message is not None:

        message.content = payload.content
        message.is_edited = True

        await session.commit()

        return message
    else:
        return None
    

async def delete_message(message_uid: str, session: AsyncSession):

    message = await get_message(message_uid, session)

    if message is not None:

        await session.delete(message)

        await session.commit()
    
    else:
        return None



async def mark_as_read(message_uid: str, session: AsyncSession):

    message = await get_message(message_uid, session)

    if message:
        message.is_read = True

        await session.commit()
        await session.refresh(message)
        return message
    
    return None