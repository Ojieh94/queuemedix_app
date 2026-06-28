import uuid
import cloudinary.uploader
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models import HospitalMedia
from sqlalchemy.orm import selectinload
from collections.abc import Sequence


async def create_hospital_media(
    *,
    hospital_uid: uuid.UUID,
    file_url: str,
    public_id: str,
    caption: str,
    display_order: int,
    is_cover: bool,
    width: int,
    height: int,
    file_size: int,
    session: AsyncSession,
) -> HospitalMedia:
    """
    Create a hospital media record.
    """

    if is_cover:
        stmt = (
            update(HospitalMedia)
            .where(HospitalMedia.hospital_uid == hospital_uid) #type: ignore
            .values(is_cover=False)
        )
        await session.execute(stmt)

    media = HospitalMedia(
        hospital_uid=hospital_uid,
        file_url=file_url,
        public_id=public_id,
        caption=caption,
        display_order=display_order,
        is_cover=is_cover,
        width=width,
        height=height,
        file_size=file_size
    )

    session.add(media)

    await session.commit()
    await session.refresh(media)

    return media





async def get_hospital_medias(
    hospital_uid: uuid.UUID,
    session: AsyncSession,
) -> Sequence[HospitalMedia]:
    """
    Retrieve all media belonging to a hospital.
    """

    stmt = (
        select(HospitalMedia)
        .where(HospitalMedia.hospital_uid == hospital_uid)
        .options(
            selectinload(HospitalMedia.hospital)
        )
        .order_by(
            HospitalMedia.is_cover.desc(),
            HospitalMedia.display_order.asc(),
        )
    )

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_hospital_media(media_uid: uuid.UUID, hospital_uid: uuid.UUID, session: AsyncSession):
    """Return a media by its ID"""

    stmt = select(HospitalMedia).where(HospitalMedia.uid == media_uid, HospitalMedia.hospital_uid ==hospital_uid)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def delete_hospital_media(
    hospital_uid: uuid.UUID,
    media_uid: uuid.UUID,
    session: AsyncSession,
):
    media_to_delete = await get_hospital_media(
        media_uid,
        hospital_uid,
        session,
    )

    if not media_to_delete:
        return None

    # Delete from Cloudinary first
    result = cloudinary.uploader.destroy(
        media_to_delete.public_id
    )

    if result.get("result") not in ("ok", "not found"):
        raise Exception("Failed to delete image from Cloudinary")

    # Delete from database
    await session.delete(media_to_delete)
    await session.commit()

    return True