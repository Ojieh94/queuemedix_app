from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import Admin, AdminType, User
from src.app.core.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.app.services import user as user_service
from src.app.database.main import get_session
from src.app.core import errors

user_router = APIRouter(prefix="/users",
    tags=['User']
)
access_token_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(["admin"]))


@user_router.get('/', response_model=List[User], dependencies=[role_checker])
async def get_all_users(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: Admin = Depends(get_current_user)):
    
    """Protected endpoint for super admins to get all users"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    users = await user_service.get_all_users(skip=skip, limit=limit, session=session)

    return users

@user_router.get('/{user_id}', dependencies=[role_checker])
async def get_user_by_id(user_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    
    """Protected endpoint for super admins to get a user by uuid"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()

    user = await user_service.get_user_by_id(user_id=user_id, session=session)

    if user:
        return user
    else:
        raise errors.UserNotFound

@user_router.delete('/{user_id}', dependencies=[role_checker])
async def delete_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(get_current_user)):
    
    """Protected endpoint for super admins to delete a user"""

    if current_user.admin_type != AdminType.SUPER_ADMIN:

        raise errors.RoleCheckAccess()
    
    user_to_delete = await user_service.delete_user(user_uid=user_id, session=session)

    if user_to_delete is None:
        raise errors.UserNotFound()
    
    else:
        return {"Message": "User deleted successfully"}
