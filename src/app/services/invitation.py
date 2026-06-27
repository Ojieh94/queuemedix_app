import secrets
import uuid
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
from src.app.models import SignupLink, AdminType, PractitionerType


async def admin_invitation(email: str, notes: str, admin_type: AdminType, hospital_uid: uuid.UUID, session: AsyncSession, department_uid: uuid.UUID):
    token = secrets.token_urlsafe(32)

    signup_link = SignupLink(token=token, email=email, admin_type=admin_type, hospital_uid=hospital_uid, notes=notes, department_uid=department_uid)

    session.add(signup_link)
    await session.commit()
    
    return token

async def practitioner_invitation(email: str, notes: str, type: PractitionerType, hospital_uid: uuid.UUID, department_uid: uuid.UUID, session: AsyncSession):
    token = secrets.token_urlsafe(32)

    signup_link = SignupLink(token=token, email=email, practitioner_type=type, hospital_uid=hospital_uid, notes=notes, department_uid=department_uid)

    session.add(signup_link)
    await session.commit()
    
    return token

#background task for periodic cleanup
async def delete_expired_tokens(session: AsyncSession):
    expired_time = datetime.now() - timedelta(hours=24)

    result = await session.execute(select(SignupLink).where(SignupLink.created_at < expired_time))

    await session.delete(result)
    await session.commit()