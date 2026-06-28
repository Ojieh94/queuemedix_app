from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, UploadFile, status, HTTPException
from src.app.core.dependencies import get_current_user
from src.app.models import User
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.database.main import get_session
from src.app.core import errors, validate_upload
from src.app.schemas import HospitalMediaRead
from src.app.services import hospital_media, upload_service, hospital as hp_service


"""
create an appointment
list appointments
list patient appointment
get appointment by id
get uncompleted appointment
cancel an appointment
check patient pending appointment
switch apointment status
"""

media_router = APIRouter(
    tags=['Hospital Media']
)

@media_router.post("/hospitals/media", response_model=HospitalMediaRead, status_code=status.HTTP_201_CREATED,)
async def upload_hospital_media(
    caption: str | None = Form(None),
    display_order: int = Form(0),
    is_cover: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not current_user.hospital:
        raise errors.NotAuthorized()
    
    await validate_upload.validate_upload(
        file=file,
        allowed_types={
            "image/jpeg",
            "image/png",
            "image/webp",
        },
        max_size=5 * 1024 * 1024,
    )

    upload = await upload_service.upload_hospital_media(
        file=file,
        folder="queuemedix/hospital_media",
    )

    media = await hospital_media.create_hospital_media(
        hospital_uid=current_user.hospital.uid,
        file_url=upload["url"],
        public_id=upload["public_id"],
        caption=caption, #type: ignore
        display_order=display_order,
        is_cover=is_cover,
        session=session,
    )

    return media


@media_router.get("/hospitals/media", status_code=status.HTTP_200_OK, response_model=List[HospitalMediaRead])
async def get_hospital_medias(hospital_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):

    hospital = await hp_service.get_single_hospital(hospital_uid, session)
    if not hospital:
        raise errors.HospitalNotFound()
    
    medias = await hospital_media.get_hospital_medias(hospital_uid, session)

    return medias


@media_router.get("/hospitals/media/{media_uid}", status_code=status.HTTP_200_OK, response_model=HospitalMediaRead)
async def get_hospital_media(media_uid: uuid.UUID, session: AsyncSession=Depends(get_session), current_user: User = Depends(get_current_user)):

    if not current_user.hospital:
        raise errors.HospitalNotFound()

    media = await hospital_media.get_hospital_media(media_uid, current_user.hospital.uid, session)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    return media


@media_router.delete("/hospitals/media/{media_uid}")
async def delete_hospital_media(media_uid: uuid.UUID, session: AsyncSession=Depends(get_session), current_user: User=Depends(get_current_user)):

    if not current_user.hospital:
        raise errors.HospitalNotFound()
    
    media = await hospital_media.get_hospital_media(media_uid, current_user.hospital.uid, session)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    await hospital_media.delete_hospital_media(current_user.hospital.uid, media.uid, session)

    return {"message": "Media deleted successfully!"}
    
    