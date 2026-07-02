from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from src.app.core.dependencies import get_current_user
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app import schemas, models
from src.app.services import hospital as hp_service, admins as ad_service, notification, review
from src.app.core import errors, permissions
from src.app.database.main import get_session
from fastapi import UploadFile, File
from src.app.services.upload_service import (
    upload_cover_image,
)

hp_router = APIRouter(
    tags=['Hospitals']
)

"""
list hospitals
get a single hospital by name
update hospital details
delete/remove hospital
"""

@hp_router.patch('/hospitals/profile-update', status_code=status.HTTP_200_OK, response_model=schemas.HospitalRead)
async def update_hospital_profile(hospital_uid: uuid.UUID, payload: schemas.HospitalProfileUpdate, session: AsyncSession = Depends(get_session), current_user: models.Hospital = Depends(get_current_user)):

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
async def get_all_hospitals(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    location: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):

    hospitals = await hp_service.get_hospitals(skip, limit, session, search=search, location=location)

    return hospitals


@hp_router.get("/hospitals/by-location", status_code=status.HTTP_200_OK, response_model=List[schemas.HospitalRead])
async def get_hospitals_by_location(
    location: str,
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user)
):
    """Return hospitals whose address or state matches the requested location."""

    hospitals = await hp_service.get_hospitals(skip, limit, session, search=None, location=location)

    return hospitals

#assign a return value of doctors when doctor route is availble
#
#response_model=List[schemas.HospitalDoctors]

@hp_router.get('/hospitals/practitioners', status_code=status.HTTP_200_OK, response_model=List[schemas.PractitionerRead])
async def view_hospital_practitioners(hospital_uid: uuid.UUID, availability: bool | None = None, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    practitioners = await hp_service.view_hospital_practitioners(hospital_uid, availability, session)

    return practitioners


@hp_router.get('/hospitals/hospital-appointments', status_code=status.HTTP_200_OK, response_model=List[schemas.AppointmentRead])
async def view_hospital_appointments(hospital_uid: uuid.UUID, status: models.ViewAppointmentStatus, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    #assigning access
    permissions.can_update_medical_record(current_user, hospital_uid)
    
    if status == models.ViewAppointmentStatus.ALL:
        status = None #type: ignore
        
    #retrieving hospital appointments    
    appointments = await hp_service.view_hospital_appointments(hospital_uid, status, session) #type: ignore

    return appointments


@hp_router.get('/hospitals/single-hospital', status_code=status.HTTP_200_OK, response_model=schemas.HospitalRead)
async def get_single_hospital(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    return hospital


@hp_router.get('/hospitals/appointment-stats', status_code=status.HTTP_200_OK, response_model=schemas.HospitalAppointmentStats)
async def get_hospital_appointment_stats(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    stats = await hp_service.get_hospital_appointment_stats(hospital_uid, session)

    return stats


@hp_router.post('/hospitals/ratings', status_code=status.HTTP_200_OK, response_model=schemas.HospitalRead)
async def rate_hospital(hospital_uid: uuid.UUID, payload: schemas.HospitalRatingCreate, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()

    updated_hospital = await hp_service.rate_hospital(hospital_uid, current_user.uid, payload.rating, session)

    return updated_hospital


@hp_router.delete('/hospitals/delete-hospital', status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    #hospital availability check
    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()
    
    #assigning access
    if current_user.role != models.UserRoles.ADMIN and current_user.uid != hospital.user_uid:
        raise errors.NotAuthorized()
    
    await hp_service.delete_hospital(hospital_uid, session)



@hp_router.patch('/hospitals/assign-duty', status_code=status.HTTP_200_OK)
async def assign_duty(admin_uid: uuid.UUID, payload: schemas.AssignAdminDuty, session: AsyncSession = Depends(get_session), current_user: models.User = Depends(get_current_user)):

    """
    Helps hospitals assign duties to department admins.
    Example: notes = "Handle prescriptions for ulceric patients"
    """

    admin = await ad_service.get_admin(admin_uid, session)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    #access control
    permissions.can_access_medical_records(current_user, admin.hospital_uid) #type: ignore

    #assign duty
    await hp_service.assign_duties_to_department_admin(admin_uid, payload, session)

    #Notify the admin
    await notification.send_notification(session, admin_uid, {
        "title": "New Notification",
        "body": f"Hello {admin.user.username}, Your new duty is '{payload.notes}'.",
        "data": {"hospital_uid": str(admin.hospital_uid)}
    })

    return {"message": "Duty has been assigned successfully"}


@hp_router.patch(
    "/cover_image",
    response_model=schemas.HospitalRead,
)
async def update_cover_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(
        get_current_user
    ),
    session: AsyncSession = Depends(get_session),
):
    # validate image
    if not file.content_type.startswith( #type: ignore
        "image/"
    ):
        raise errors.FileUpload()

    # upload image
    image_url = (
        await upload_cover_image(file)
    )

    # update hospital cover image
    current_user.hospital.cover_image = image_url #type: ignore

    await session.commit()

    await session.refresh(current_user)

    return current_user

@hp_router.get("/hospitals/hospital_patients", status_code=status.HTTP_200_OK, response_model=List[schemas.HospitalPatientRead])
async def get_hospital_patients(session: AsyncSession=Depends(get_session), current_user:models.User = Depends(get_current_user)):
    
    if not current_user.hospital:
        raise errors.HospitalNotFound()
    
    hospital_patients = await hp_service.get_hospital_patients(current_user.hospital.uid, session)

    return hospital_patients


@hp_router.get("/hospitals/reviews", response_model=list[schemas.ReviewRead], tags=["Reviews"])
async def get_hospital_reviews(offset: int = 0, limit: int = 20, current_user: models.User=Depends(get_current_user), session: AsyncSession=Depends(get_session),):

    if not current_user.hospital:
        raise errors.NotAuthorized()

    reviews = await review.get_hospital_reviews(
        hospital_uid=current_user.hospital.uid,
        offset=offset,
        limit=limit,
        session=session,
    )

    return reviews