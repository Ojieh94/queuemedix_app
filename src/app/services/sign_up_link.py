import secrets
from typing import Optional
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
from src.app.models import SignupLink, AdminType, User


async def create_signup_link(email: str, notes: str, admin_type: AdminType, current_user: User, session: AsyncSession, department_uid: Optional[str] = None) -> str:
    token = secrets.token_urlsafe(32)

    signup_link = SignupLink(token=token, email=email, admin_type=admin_type, hospital_uid=str(current_user.hospital.uid), notes=notes, department_uid=department_uid)

    session.add(signup_link)
    await session.commit()
    
    return token

#background task for periodic cleanup
async def delete_expired_tokens(session: AsyncSession):
    expired_time = datetime.now() - timedelta(hours=24)

    result = await session.execute(select(SignupLink).where(SignupLink.created_at < expired_time))

    await session.delete(result)
    await session.commit()