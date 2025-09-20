from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import Admin, AdminType, User
from src.app.core.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.app.schemas import AdminProfileUpdate
from src.app.services import admins as admin_service
from src.app.database.main import get_session
from src.app.core import errors

admin_router = APIRouter(prefix="/admins",
                        tags=['Admins']
                        )
access_token_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(["admin"]))


@admin_router.get('/', response_model=List[User], dependencies=[role_checker])
async def get_admins(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for super admins to get all admins"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    users = await admin_service.get_admins(skip=skip, limit=limit, session=session)

    return users


@admin_router.get('/{admin_id}', dependencies=[role_checker])
async def get_admin(admin_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for super admins to get an admin by uuid"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    user = await admin_service.get_admin(admin_id=admin_id, session=session)

    if user:
        return user
    else:
        raise errors.UserNotFound()
    

@admin_router.patch("/{admin_id}", dependencies=[role_checker])
async def update_admin_profile(admin_id: str, update_data: AdminProfileUpdate, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for updating admin profile"""

    if current_user.uid != admin_id:
        raise errors.NotAuthorized()

    updated_admin = await admin_service.update_admin(admin_id=admin_id, update_data=update_data, session=session)

    if updated_admin is None:
        raise errors.UserNotFound()

    else:
        return updated_admin



@admin_router.delete('/{admin_id}', dependencies=[role_checker])
async def delete_admin(admin_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    """Protected endpoint for super admins to delete admin user"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    admin_to_delete = await admin_service.delete_admin(admin_uid=admin_id, session=session)

    if admin_to_delete is None:
        raise errors.UserNotFound()

    else:
        return {"Message": "Admin deleted successfully"}
