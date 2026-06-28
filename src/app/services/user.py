import uuid

from sqlalchemy import exists
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models import User, Hospital, Practitioner


async def get_username(username: str, session: AsyncSession):

    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_user_email(email: str, session: AsyncSession):

    stmt = (
        select(User)
        .where(User.email == email)
        .options(
            selectinload(User.admin),
            selectinload(User.patient),
            selectinload(User.hospital).selectinload(Hospital.admin),
            selectinload(User.hospital).selectinload(Hospital.department),
            selectinload(User.practitioner).selectinload(Practitioner.department),
            selectinload(User.practitioner).selectinload(Practitioner.hospital),
        )
    )
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_login_data(username: str, email: str, session: AsyncSession):

    if username:
        user = await get_username(username, session)
        if user:
            return user
    if email:
        user = await get_user_email(email, session)
        return user
    return None


async def update_user_info(user: User, user_data: dict, session: AsyncSession):

    for k, v in user_data.items():
        setattr(user, k, v)

    await session.commit()

    return user


async def get_all_users(skip: int, limit: int, session: AsyncSession):

    stmt = select(User).offset(skip).limit(limit)
    result = await session.execute(stmt)

    return result.scalars().all()


async def get_user_by_id(user_id: uuid.UUID, session: AsyncSession):

    stmt = select(User).where(User.uid == user_id)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def delete_user(user_uid: uuid.UUID, session: AsyncSession):

    user = await get_user_by_id(user_id=user_uid, session=session)

    if user is not None:

        await session.delete(user)

        await session.commit()

        return {}

    else:
        return None


async def username_exists(username: str, session: AsyncSession) -> bool:
    stmt = select(exists().where(User.username == username)) #type: ignore
    result = await session.execute(stmt)
    return result.scalar_one()  # True or False
