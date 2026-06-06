from fastapi import APIRouter, Depends, status, HTTPException
from src.app.core.dependencies import  get_current_user
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import User
from src.app.services import queue, patients
from src.app.database.main import get_session
from src.app.core import errors

"""
get patient's queue status
"""

queue_router = APIRouter(
    tags=['Queue']
)



@queue_router.get('/queues/me', status_code=status.HTTP_200_OK)
async def get_my_queue_status(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    patient = await patients.get_patient_by_user_uid(current_user.uid, session)

    if not patient:
        raise errors.PatientNotFound()
    
    queue_entry = await queue.get_active_queue_entry_by_patient_uid(session, patient.uid)

    if not queue_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active queue found."
        )
    

    patients_ahead = await queue.count_patients_ahead(session, queue_entry.queue_uid, queue_entry.queue_number)

    position = patients_ahead + 1

    return {
    "queue_entry_uid": queue_entry.uid,
    "queue_number": queue_entry.queue_number,
    "position": position,
    "patients_ahead": patients_ahead,
    "status": queue_entry.status,
    "hospital_name": queue_entry.queues.hospital.hospital_name,
    "queue_name": queue_entry.queues.name
    }

@queue_router.get('/queues', status_code=status.HTTP_200_OK)
async def get_queues(session=Depends(get_session)):
    return await queue.get_queues(session)