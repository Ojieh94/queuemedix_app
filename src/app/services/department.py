import uuid
from collections.abc import Sequence
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from typing import Optional
from src.app.models import Department, Hospital
from src.app.schemas import DepartmentCreate, DepartmentUpdate

"""
create department
list all available department
list department by id
update department
delete department
"""

async def create_department(payload: DepartmentCreate, hospital_uid: uuid.UUID, session: AsyncSession) -> Department:

    new_department = Department(**payload.model_dump(), hospital_uid=hospital_uid)

    session.add(new_department)
    await session.commit()
    await session.refresh(new_department)

    return new_department


async def list_departments(skip: int, limit: int, search: Optional[str], session: AsyncSession):
    stmt = select(Department).options(selectinload(Department.hospital).selectinload(Hospital.user))

    if search:
        stmt = stmt.filter(Department.name.ilike(f"%{search}%")) #type: ignore
 
    stmt = stmt.order_by(Department.name.asc()).offset(skip).limit(limit) #type: ignore
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_department_by_id(department_uid: uuid.UUID, session: AsyncSession) -> Department:

    return (await session.execute(select(Department).where(Department.uid == department_uid).options(selectinload(Department.hospital).selectinload(Hospital.user)))).scalar_one()


async def get_hospital_departments(hospital_uid: uuid.UUID, session: AsyncSession) -> Sequence[Department]:

    result = await session.execute(select(Department).where(Department.hospital_uid == hospital_uid).options(selectinload(Department.hospital).selectinload(Hospital.user)))
    
    return result.scalars().all()


async def update_department(department_uid: uuid.UUID, payload: DepartmentUpdate, session: AsyncSession) -> Department | None:

    department_to_update = await get_department_by_id(department_uid, session)

    if department_to_update:

        payload_dict = payload.model_dump(exclude_unset=True)

        for k, v in payload_dict.items():
            setattr(department_to_update, k, v)
            
        await session.commit()
        await session.refresh(department_to_update)

        return department_to_update
    else:
        return None


async def delete_department(department_uid: uuid.UUID, session: AsyncSession):

    department = await get_department_by_id(department_uid, session)
    
    if not department:
        return None
    
    await session.delete(department)
    await session.commit()