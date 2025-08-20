from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models import User


async def get_username(username: str, session: AsyncSession):

    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()

async def get_user_email(email: str, session: AsyncSession):

    stmt = select(User).where(User.email == email)
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