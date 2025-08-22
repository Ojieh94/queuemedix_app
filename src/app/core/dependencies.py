from fastapi.security import HTTPBearer
from fastapi import Request, Depends, HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import List, Any
from src.app.database.main import get_session
from src.app.models import User
from src.app.core.utils import verify_access_token, validate_refresh_token_jti, get_blacklisted_token_jti
from src.app.services import user as user_service
from src.app.core import errors


class AccessPass(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request, session: AsyncSession=Depends(get_session)) -> HTTPAuthorizationCredentials | None:
        
        creds = await super().__call__(request)

        token = creds.credentials

        try:
            token_data = verify_access_token(token)
        except Exception:
            raise errors.InvalidToken()
        
        if not token_data:
            raise errors.InvalidToken()
        
        if token_data.get('jti') is None:
            raise errors.MissingJTI()
        
        #check if token has been revoked
        token_jti = token_data.get('jti')
        blacklisted_token = await get_blacklisted_token_jti(token_jti, session)
        if blacklisted_token:
            raise errors.TokenRevoked()
        
        await self.verify_token_data(token_data, session)

        return token_data

    async def verify_token_data(self, token_data):
        raise NotImplementedError("Override this method in child classes")


class AccessTokenBearer(AccessPass):

    async def verify_token_data(self, token_data: dict, session: AsyncSession):
        
        if token_data and token_data.get('refresh'):
            raise errors.AccessToken

class RefreshTokenBearer(AccessPass):

    async def verify_token_data(self, token_data: dict, session: AsyncSession):
        
        if token_data and not token_data.get('refresh'):
            raise errors.RefreshToken()
        
        refresh_jti = token_data.get('jti')
        if not refresh_jti:
            raise errors.MissingJTI()
        
        await validate_refresh_token_jti(refresh_jti, session)


async def get_current_user(token_details: dict = Depends(AccessTokenBearer()), session: AsyncSession=Depends(get_session)):

    user_email = token_details['user']['email']

    user = await user_service.get_user_email(user_email, session)

    if not user:
        raise errors.InvalidCred()

    if not user.is_active:
        raise errors.AccountNotVerified()
    
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = [role for role in allowed_roles]

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        
        user_role = current_user.role
        if user_role in self.allowed_roles:
            return True
        
        raise errors.RoleCheckAccess()

refresh_token = RefreshTokenBearer()