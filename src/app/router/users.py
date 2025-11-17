from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.models import Admin, AdminType, User, UserRoles
from src.app.core.dependencies import AccessTokenBearer, get_current_user, require_super_admin
from src.app.services import user as user_service
from src.app.database.main import get_session
from src.app.core import errors

user_router = APIRouter(prefix="/users",
    tags=['User']
)
access_token_bearer = AccessTokenBearer()


@user_router.get("/check-username")
async def check_username_availability(
    username: str = Query(..., min_length=3, max_length=50),
    session: AsyncSession = Depends(get_session)
):
    """Endpoint to check if a username is already taken. To be used during user registration."""
    
    existing_user = await user_service.username_exists(username=username, session=session)

    return {"available": not existing_user}

@user_router.get('/', response_model=List[User])
async def get_all_users(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session),
                        current_user: User = Depends(require_super_admin)):
    
    """Protected endpoint for super admins to get all users"""

    users = await user_service.get_all_users(skip=skip, limit=limit, session=session)

    return users

@user_router.get('/{user_id}', response_model=User)
async def get_user_by_id(user_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(require_super_admin)):
    
    """Protected endpoint for super admins to get a user by uuid"""


    user = await user_service.get_user_by_id(user_id=user_id, session=session)

    if user:
        return user
    else:
        raise errors.UserNotFound

@user_router.delete('/{user_id}', status_code=200)
async def delete_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: Admin = Depends(require_super_admin)):

    """Protected endpoint for super admins to delete a user"""
    
    user_to_delete = await user_service.delete_user(user_uid=user_id, session=session)

    if user_to_delete is None:
        raise errors.UserNotFound()
    
    else:
        return {"Message": "User deleted successfully"}
