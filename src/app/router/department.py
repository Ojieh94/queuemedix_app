from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from src.app.core.dependencies import get_current_user
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.schemas import DepartmentRead, DepartmentCreate, DepartmentUpdate
from src.app.models import User, Department, AdminType
from src.app.services import department as dept_service, hospital as hp_service
from src.app.database.main import get_session
from src.app.core import errors, permissions

dept_router = APIRouter(
    tags=['Departments']
)

"""
create department
list all available department
list department by id
update department
delete department
"""

@dept_router.post('/hospitals/{hospital_uid}/departments', status_code=status.HTTP_201_CREATED, response_model=Department, tags=['Hospitals'])
async def add_department(hospital_uid: str, payload: DepartmentCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    #check hospital availability
    hospital = await hp_service.get_single_hospital(hospital_uid, session)

    if not hospital:
        raise errors.HospitalNotFound()

    # #authorization checks
    permissions.check_department_permission(current_user, hospital.uid)

    department = await dept_service.create_department(payload, hospital_uid, session)
    
    return department


@dept_router.get('/hospitals/departments', status_code=status.HTTP_200_OK, response_model=List[Department], tags=['Hospitals'])
async def list_departments(skip: int = 0, limit: int = 10, search: Optional[str] = "", session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """
    Patients should be view all departments on hospitals accross the platform.
    This will help them identify which hospital to book appointment with
    """

    departments = await dept_service.list_departments(skip, limit, search, session)

    #access control
    permissions.list_department_permission(current_user, departments)
    
    return departments


@dept_router.get('/departments/{department_uid}', status_code=status.HTTP_200_OK, response_model=Department)
async def get_department(department_uid: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    department = await dept_service.get_department_by_id(department_uid, session)
    
    if not department:
        raise errors.DepartmentNotFound()
    
    #access control
    permissions.get_department_permission(current_user, department)
    
    return department


@dept_router.patch('/departments/{department_uid}', status_code=status.HTTP_202_ACCEPTED, response_model=Department)
async def update_department(department_uid: str, payload: DepartmentUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    department = await dept_service.get_department_by_id(department_uid, session)

    if not department:
        raise errors.DepartmentNotFound()
    
    #access control
    permissions.update_department_permission(current_user, department)
    
    updated_department = await dept_service.update_department(department_uid, payload, session)

    return updated_department


@dept_router.delete('/departments/{department_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_department(department_uid: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    department_to_remove = await dept_service.get_department_by_id(department_uid, session)
    
    if not department_to_remove:
        raise errors.DepartmentNotFound()
    
    #access control check
    permissions.check_department_permission(current_user, department_to_remove.hospital_uid)
    
    await dept_service.delete_department(department_uid, session)