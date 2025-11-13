from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.app.models import Admin
from src.app.schemas import AdminProfileUpdate, RegisterAdminUser


async def get_admin(admin_id: str, session: AsyncSession):

   stmt = select(Admin).where(Admin.uid == admin_id)
   result = await session.execute(stmt)

   return result.scalar_one_or_none()
    

async def get_admins(skip: int, limit: int, session: AsyncSession):

   stmt = select(Admin).offset(skip).limit(limit)
   result = await session.execute(stmt)

   return result.scalars().all()

async def get_hospital_admins(hospital_id: str, session: AsyncSession):

   stmt = select(Admin).where(Admin.hospital_uid == hospital_id)
   result = await session.execute(stmt)

   return result.scalars().all()

async def update_admin(admin_id: str, update_data: AdminProfileUpdate, session: AsyncSession):
    admin_to_update = await get_admin(admin_id=admin_id, session=session)

    if admin_to_update is not None:
      update_data_dict = update_data.model_dump(exclude_unset=True)

      for k, v in update_data_dict.items():
                setattr(admin_to_update, k, v)

      await session.commit()
      await session.refresh(admin_to_update)

      return admin_to_update
    else:
      return None


async def delete_admin(admin_id: str, session: AsyncSession):

    admin = await get_admin(admin_id=admin_id, session=session)

    if admin is not None:

        await session.delete(admin)

        await session.commit()

        return {}

    else:
        return None

