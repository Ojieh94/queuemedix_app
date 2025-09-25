from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models import Message
from src.app.schemas import MessageCreate, MessageUpdate, MessageRead, DataPlusMessage
from src.app.services import message as m_service, user as user_service
from src.app.database.main import get_session
from src.app.websocket.connection_manager import manager
from src.app.models import User
from src.app.core.dependencies import get_current_user
from src.app.core import errors

router = APIRouter(tags=['Messages'])
ws_router = APIRouter(tags=['Messages', 'Websockets'])


@router.post("/messages", status_code=status.HTTP_201_CREATED, response_model=DataPlusMessage)
async def send_message(
    payload: MessageCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new message via REST.
    - sender = current_user (taken from JWT)
    - receiver = from payload
    - content = from payload
    """

    user = await user_service.get_user_by_id(payload.receiver_uid, session)

    #Check if receiver exits
    if not user:
        raise errors.UserNotFound()
    
    message = await m_service.send_message(payload, current_user, session)

    return {
        "message": f"Hey {current_user.username}, you've started a DM with {user.username} - Say Hi",
        "data": message
    }


@ws_router.websocket("/ws/dm/{hospital_uid}")
async def websocket_dm(
    websocket: WebSocket,
    hospital_uid: str
):
    """
    WebSocket endpoint for doctor-patient DM.
    Only listens for new messages broadcasted to this room.
    Clients do NOT send messages here (REST handles that).
    """
    await manager.connect(websocket, channel="dm", room_id=hospital_uid)

    try:
        while True:
            await websocket.receive_text()  # Keep alive (or ping/pong)
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="dm", room_id=hospital_uid)


#Get chat history
@router.get("/chat/history/{other_user_id}", response_model=list[MessageRead])
async def get_chat_history(
    other_user_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
   
    """Fetch chat history between the logged-in user and another user."""

    message = await m_service.get_chat_history(other_user_id, session, current_user)

    return message


#Edit message
@router.patch("/messages/{message_uid}", response_model=MessageRead)
async def edit_message(message_uid: str, payload: MessageUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Edit chat message."""

    message = await m_service.get_message(message_uid, session)

    if not message:
        raise errors.MessageNotFound()
    
    if current_user.uid != message.sender_uid:
        raise errors.NotAuthorized()
    
    edited_message = await m_service.edit_message(message_uid, payload.content, session)

    return edited_message


#Delete message
@router.delete("/messages/{message_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_uid: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Delete chat message."""

    message = await m_service.get_message(message_uid, session)

    if not message:
        raise errors.MessageNotFound()
    
    if current_user.uid != message.sender_uid:
        raise errors.NotAuthorized()
    
    await m_service.delete_message(message_uid, session)


#Mark message as read
@router.patch("/messages/{message_uid}/read_receipt", response_model=MessageRead)
async def mark_message_as_read(message_uid: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """Use this endpont to toggle "is_read" field to "True" when a message is opened"""

    message = await m_service.get_message(message_uid, session)

    if not message:
        raise errors.MessageNotFound()
    
    if current_user.uid != message.receiver_uid:
        raise errors.NotAuthorized()
    
    return await m_service.mark_as_read(message_uid, session)