import uuid
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio.session import AsyncSession
from datetime import timedelta, datetime, timezone
from src.app.schemas import RegisterUser, LoginData, EmailModel, RegisterAdminUser
from src.app.database.main import get_session
from src.app.models import User, AdminType
from src.app.services import user as user_service, auth as auth_service, sign_up_link as link_service
from src.app.core.dependencies import get_current_user, refresh_token
from src.app.core import celery, errors, settings, redis, mails
from src.app import schemas
from src.app.core.utils import (
    verify_password, 
    create_access_token, 
    save_refresh_token_jti,
    create_token_blacklist,
    revoke_refresh_token,
    delete_blacklisted_token,
    get_blacklisted_token_jti,
    verify_access_token,
    validate_refresh_token_jti,
    create_url_safe_token,
    decode_url_safe_token,
    decode_password_url_safe_token,
    hash_password
    )



auth_router = APIRouter(
    tags=["Authentication"]
)

REFRESH_TOKEN_EXPIRY = 2

auth_scheme = HTTPBearer()

@auth_router.post('/auth/register', status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterUser, session: AsyncSession = Depends(get_session)):

    """
    Only these roles can use this endpoint:
    Roles: "doctor", "hospital", "patient"
    
    """
    email = payload.email

    existing_user = await user_service.get_user_email(payload.email, session)

    if existing_user:
        raise errors.UserAlreadyExists()
    
    new_user = await auth_service.register_user(payload=payload, session=session)

    token = create_url_safe_token({"email": email})

    mails.send_verification_email(email, token)

    # Save the token in Redis
    await redis.save_email_verification_token(email, token)

    return {
        "message": f"{payload.role.capitalize()}'s account created successfully! Please check your email to verify your account.",
        "user": new_user 
    }


@auth_router.post("/auth/signup_link", tags=["Unique Signup Link Generator"])
async def generate_link(email: str, notes: str, admin_type: AdminType, request: Request, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):

    token = await link_service.create_signup_link(email, notes, admin_type, current_user, session)

    # Construct the full URL based on request
    base_url = str(request.base_url).rstrip("/")
    signup_path = "/auth/signup/hospital_admin"
    signup_link = f"{base_url}{signup_path}?token={token}"

    #forward the link to the admin's email
    mails.hospital_admin_invite(email, current_user.hospital.hospital_name, signup_link)

    return JSONResponse(
        content={
            "message": "Your link has been created and forwarded to the admin's email successfully.",
            "data": signup_link
        }
    )



### ADMIN SESSION
@auth_router.post("/auth/signup/hospital_admin", status_code=status.HTTP_201_CREATED)
async def admin_signup(payload: RegisterAdminUser, token: str, session: AsyncSession = Depends(get_session)):

    """
    This endpoint is for admins to signup with generated link by hospital
    Roles: "hospital_admin", "department_admin"
    
    """
    email = payload.email

    existing_user = await user_service.get_user_email(payload.email, session)

    if existing_user:
        raise errors.UserAlreadyExists()
    
    new_user = await auth_service.register_admin(payload, token, session)

    return {
        "message": f"Hello! {payload.username} your account has been created and activated successfully! Please proceed to login.",
        "user": new_user 
    }


@auth_router.post("/auth/signup/queue_medix_admin", status_code=status.HTTP_201_CREATED)
async def super_admin_signup(payload: RegisterAdminUser, token: str, session: AsyncSession = Depends(get_session)):

    """
    This endpoint is for admins to signup with generated link by hospital
    Roles: "hospital_admin", "department_admin"
    
    """
    email = payload.email

    existing_user = await user_service.get_user_email(payload.email, session)

    if existing_user:
        raise errors.UserAlreadyExists()
    
    new_user = await auth_service.register_super_admin(payload, session)

    token = create_url_safe_token({"email": email})

    mails.send_verification_email(email, token)

    # Save the token in Redis
    await redis.save_email_verification_token(email, token)

    return {
        "message": f"Hello! {payload.username} your account has been created successfully! Please check your email for verification link.",
        "user": new_user 
    }


@auth_router.post('/auth/signin', status_code=status.HTTP_200_OK)
async def login(payload: LoginData, session: AsyncSession=Depends(get_session)):

    username_or_email = payload.username
    password = payload.password

    user = await user_service.get_login_data(username_or_email, username_or_email, session)

    if not user:
        raise errors.InvalidEmailOrPassword()

    if not user.is_active:
        raise errors.AccountNotVerified(user)

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


@auth_router.get('/auth/me', status_code=status.HTTP_200_OK, response_model=schemas.UserReadMe)
async def current_user(me: User=Depends(get_current_user)):

    """This endpoint returns the currently authenticated user's info"""
    return me


@auth_router.post('/auth/logout', status_code=status.HTTP_200_OK)
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
            raise errors.UserLoggedOut()

        session_id = token_data.get('session_id')
        if not session_id:
            raise errors.MissingSessionID()
        
        await create_token_blacklist(token, session)

        await revoke_refresh_token(session_id, session)

    except ValueError:
        raise errors.InvalidToken()
    
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
    
    raise errors.RefreshToken()


@auth_router.get('/auth/email_verification/{token}', status_code=status.HTTP_200_OK)
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):

    token_data = decode_url_safe_token(token)

    if not token_data:
        raise errors.InvalidToken()

    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_email(user_email, session)

        if not user:
            raise errors.UserNotFound()
        
        await user_service.update_user_info(user, {"is_active": True}, session)

        await redis.delete_email_verification_token(user_email)

        return JSONResponse(
            content={"message": "Account has been verified successfully!"},
            status_code=status.HTTP_200_OK
        )
    
    return JSONResponse(
        content={"message": "An error occured during verification!"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


#####..........PASSWORD RESET

@auth_router.post('/auth/password-reset')
async def password_reset_request(email_data: schemas.PasswordResetRequest):
    
    email = email_data.email_address

    token = create_url_safe_token({"email": email})

    emails = [email]

    mails.send_password_reset_email(emails, token)

    return JSONResponse(
        content={"message": "Please check your email for instructions to reset your password."},
        status_code=status.HTTP_200_OK
    )

@auth_router.post('/auth/password-resets/{token}', status_code=status.HTTP_200_OK)
async def confirm_password_reset(passwd_data: schemas.ConfirmPasswordReset, token: str, session: AsyncSession = Depends(get_session)):

    new_password = passwd_data.new_password
    confirm_password = passwd_data.confirm_password

    if confirm_password != new_password:
        raise HTTPException(
            detail={"message": "Password does not match"},
            status_code=status.HTTP_403_FORBIDDEN
        )

    token_data = decode_password_url_safe_token(token)

    if not token_data:
        raise errors.InvalidToken()

    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_email(user_email, session)

        if not user:
            raise errors.UserNotFound()
        
        hashed_password = hash_password(new_password)
        
        await user_service.update_user_info(user, {"hashed_password": hashed_password}, session)

        return JSONResponse(
            content={"message": "Your password has been changed successfully!"},
            status_code=status.HTTP_200_OK
        )
    
    return JSONResponse(
        content={"message": "An error occured during verification!"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@auth_router.post('/send_email', status_code=status.HTTP_200_OK)
async def send_email(email: EmailModel):
    mail_to = email.mail_to

    mails.send_test(mail_to)

    return {"message": "email sent successfully!"}