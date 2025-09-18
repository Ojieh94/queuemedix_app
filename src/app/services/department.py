from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional, List
from src.app.models import Department
from src.app.schemas import DepartmentCreate, DepartmentUpdate

"""
create department
list all available department
list department by id
update department
delete department
"""

async def create_department(payload: DepartmentCreate, hospital_uid: str, session: AsyncSession) -> Department:

    new_department = Department(**payload.model_dump(), hospital_uid=hospital_uid)

    session.add(new_department)
    await session.commit()
    await session.refresh(new_department)

    return new_department


async def list_departments(skip: int, limit: int, search: Optional[str], session: AsyncSession) -> List[Department]:

    stmt =  select(Department).offset(skip).limit(limit)
    
    if search:
        stmt = stmt.filter(Department.name.contains(search))

    result = await session.execute(stmt)
    
    return result.scalar_one_or_none()


async def get_department_by_id(department_uid: str, session: AsyncSession) -> Department:

    return (await session.execute(select(Department).where(Department.uid == department_uid))).scalar_one_or_none()


async def update_department(department_uid: str, payload: DepartmentUpdate, session: AsyncSession) -> Department:

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


async def delete_department(department_uid: str, session: AsyncSession):

    department = await get_department_by_id(department_uid, session)
    
    if not department:
        return None
    
    await session.delete(department)
    await session.commit()