import uuid
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio.session import AsyncSession
from datetime import timedelta, datetime, timezone
from src.app.schemas import RegisterUser, LoginData
from src.app.database.main import get_session
from src.app.models import User
from src.app.services import user as user_service, auth as auth_service
from src.app.core.dependencies import get_current_user, refresh_token
from src.app.core.utils import (
    verify_password, 
    create_access_token, 
    save_refresh_token_jti,
    create_token_blacklist,
    revoke_refresh_token,
    delete_blacklisted_token,
    get_blacklisted_token_jti,
    verify_access_token,
    validate_refresh_token_jti
    )



auth_router = APIRouter(
    tags=["Authentication"]
)

REFRESH_TOKEN_EXPIRY = 2

@auth_router.post('/auth/register', status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterUser, session: AsyncSession = Depends(get_session)):

    """
    Roles: "admin", "doctor", "hospital", "patient"
    
    """

    existing_user = await user_service.get_user_email(payload.email, session)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered!"
        )
    
    new_user = await auth_service.register_user(payload=payload, session=session)

    return {
        "message": f"{payload.role.capitalize()}'s Account created successfully!",
        "user": new_user 
    }


@auth_router.post('/auth/signin', status_code=status.HTTP_200_OK)
async def login(payload: LoginData, session: AsyncSession=Depends(get_session)):

    username_or_email = payload.username
    password = payload.password

    user = await user_service.get_login_data(username_or_email, username_or_email, session)

    if user is not None:

        #Validate password
        validate_password = verify_password(password, user.hashed_password)
        
        if validate_password:

            access_jti = str(uuid.uuid4())
            refresh_jti = str(uuid.uuid4())
            session_id = str(uuid.uuid4())

            user_data = {
                "user_uid": str(user.uid),
                "username": user.username,
                "email": user.email,
                "role": user.role
            }

            #create access_token
            access_token = create_access_token(
                user_data=user_data,
                session_id=session_id,
                jti=access_jti
            )

            #create refresh_token
            refresh_token = create_access_token(
                user_data=user_data,
                expiry= timedelta(days=REFRESH_TOKEN_EXPIRY),
                refresh=True,
                session_id=session_id,
                jti=refresh_jti
            )

            #decode refresh_token
            decoded_refresh_token = verify_access_token(refresh_token)
            expires_at = datetime.fromtimestamp(decoded_refresh_token['exp'])

            #save refresh_token meta data for easy revoking
            await save_refresh_token_jti(
                jti=refresh_jti,
                session_id=session_id,
                expires_at=expires_at,
                user_uid=user.uid,
                session=session
            )

            return JSONResponse(
                content={
                    "message": f"Welcome back {user.username}",
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            )
        
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid login details!"
    )


@auth_router.get('/auth/me', status_code=status.HTTP_200_OK)
async def current_user(me: User=Depends(get_current_user)):

    """This endpoint returns the currently authenticated user's info"""
    return me



auth_scheme = HTTPBearer()
@auth_router.post('/auth/signout', status_code=status.HTTP_200_OK)
async def logout(bg_task: BackgroundTasks, credentials: HTTPAuthorizationCredentials = Depends(auth_scheme), session: AsyncSession = Depends(get_session)):

    """
    Logs the user out by revoking their access token via blacklisting.
    
    This endpoint extracts the user's bearer token from the Authorization header,
    validates it, and adds it to a blacklist to prevent further use.
    """

    token = credentials.credentials
    
    try:
        token_data = verify_access_token(token)
        
        token_jti = token_data.get('jti')

        #will not be neccessary just to control exceptions for ease dev exprience
        revoked_token = await get_blacklisted_token_jti(token_jti, session)
        if revoked_token:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="User already logged out"
            )


        session_id = token_data.get('session_id')
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is missing session_id"
            )
        
        await create_token_blacklist(token, session)

        await revoke_refresh_token(session_id, session)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    bg_task.add_task(delete_blacklisted_token, session)

    return {"Message": "User logged out successfully"}

@auth_router.get('/auth/access_token', status_code=status.HTTP_200_OK)
async def get_new_token(token_details: dict = Depends(refresh_token), session: AsyncSession=Depends(get_session)):

    """
    Generates a new access token using a valid refresh token.

    This endpoint allows users to obtain a fresh access token when the current one has expired, helping maintain an active session without requiring re-authentication.

    Access Token lasts only 15mins while Refresh token is extended to 2days.

    So please utilize this.
    """

    expiry_time = token_details['exp']

    user = token_details.get('user')
    session_id = token_details.get('session_id')
    jti = token_details.get('jti')

    await validate_refresh_token_jti(jti, session)

    if datetime.fromtimestamp(expiry_time, tz=timezone.utc) > datetime.now(tz=timezone.utc):

        new_access_token = create_access_token(
            user_data=user,
            session_id=session_id
        )

        return JSONResponse(
            content={
                "message": "new access_token",
                "access_token": new_access_token
            }
        )
    
    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        detail="Invalid or expired refresh token"
    )