from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from src.app.core.dependencies import get_current_user
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app import schemas, models
from src.app.services import hospital as hp_service
from src.app.core import errors
from src.app.database.main import get_session

hp_router = APIRouter(
    tags=['Hospitals']
)

"""
list hospitals
get a single hospital by name
update hospital details
delete/remove hospital
"""

@hp_router.patch('/hospitals/{hospital_uid}/profile', status_code=status.HTTP_200_OK, response_model=schemas.HospitalRead)
async def update_hospital_profile(hospital_uid: str, payload: schemas.HospitalProfileUpdate, session: AsyncSession = Depends(get_session), current_user: models.Hospital = Depends(get_current_user)):

    """
    Update the hospital profile with the given payload.
    Returns the updated hospital object or None if not found.
    """

    #hospital availability check
    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    #assigning access control
    if current_user.uid != hospital.user_uid:
        raise errors.NotAuthorized()
    
    #update hospital
    updated_hospital = await hp_service.update_hospital_profile(payload, hospital_uid, session)

    return updated_hospital


@hp_router.get("/hospitals", status_code=status.HTTP_200_OK, response_model=List[schemas.HospitalRead])
async def get_all_hospitals( skip: int = 0, limit: int = 10, search: Optional[str] = "", session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospitals = await hp_service.get_hospitals(skip, limit, search, session)

    return hospitals

#assign a return value of doctors when doctor route is availble
#
#response_model=List[schemas.HospitalDoctors]

@hp_router.get('/hospitals/{hospital_id}/doctors', status_code=status.HTTP_200_OK)
async def view_hospital_doctors(hospital_uid: str, availability: Optional[bool], session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    doctors = await hp_service.view_hospital_doctors(hospital_uid, availability, session)

    return doctors


@hp_router.get('/hospitals/{hospital_uid}/appointments', status_code=status.HTTP_200_OK, response_model=List[schemas.AppointmentRead])
async def view_hospital_appointments(hospital_uid: str, status: models.AppointmentStatus, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    #assigning access
    access_roles = {models.UserRoles.ADMIN, models.UserRoles.HOSPITAL, models.UserRoles.DOCTOR}

    if current_user.role not in access_roles:
        raise errors.NotAuthorized()
    
    #retrieving hospital appointments    
    appointments = await hp_service.view_hospital_appointments(hospital_uid, status, session)

    return appointments


@hp_router.get('/hospitals/{hospital_uid}', status_code=status.HTTP_200_OK, response_model=schemas.HospitalRead)
async def get_single_hospital(hospital_uid: str, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    return hospital


@hp_router.delete('/hospitals/{hospital_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital(hospital_uid: str, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    #hospital availability check
    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    #assigning access
    if current_user.role != models.UserRoles.ADMIN and current_user.uid != hospital.user_uid:
        raise errors.NotAuthorized()
    
    await hp_service.delete_hospital(hospital_uid, session)