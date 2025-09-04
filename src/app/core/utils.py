import jwt
import logging
import uuid
from sqlmodel import select, delete
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from jwt import PyJWTError, ExpiredSignatureError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer,BadSignature, SignatureExpired
from src.app.core.settings import Config
from src.app.models import RefreshToken, BlacklistedToken


ACCESS_TOKEN_EXPIRY= 15 #Time in mins(15). Please increase this while developing

pwd_context = CryptContext(
    schemes=["bcrypt"]
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool=False, session_id: str=None, jti: str=None):

    token_expiry = expiry if expiry is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRY)

    payload = {}

    payload["user"] = user_data
    payload["exp"] = int((datetime.now(timezone.utc) + token_expiry).timestamp())
    payload["refresh"] = refresh
    payload["session_id"] = session_id or str(uuid.uuid4())
    payload["jti"] = jti or str(uuid.uuid4())

    access_token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

    return access_token


def verify_access_token(token: str) -> dict:

    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )

        if "jti" not in token_data:
            raise ValueError("Error: 'jti' field not in token!")
        
        return token_data
    
    except ExpiredSignatureError:
        raise Exception("Token has expired.")
    
    except PyJWTError as e:
        raise Exception(f"Invalid token: {e}")
    

async def save_refresh_token_jti(
        jti: str,
        session_id: str,
        expires_at: datetime,
        user_uid: str,
        session: AsyncSession
    ):

    token = RefreshToken(
        jti=jti,
        session_id=session_id,
        expires_at=expires_at,
        user_uid=user_uid
    )

    session.add(token)
    await session.commit()


async def validate_refresh_token_jti(jti: str, session:AsyncSession):

    stmt = select(RefreshToken).where(
        RefreshToken.jti == jti,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now()
        )
    
    result = await session.execute(stmt)
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid of expired token"
        )
    
    return token


async def revoke_refresh_token(session_id: str, session: AsyncSession):

    stmt = select(RefreshToken).where(RefreshToken.session_id == session_id)

    result = await session.execute(stmt)

    token = result.scalar_one_or_none()

    if token:
        token.revoked = True
        await session.commit()


########.....Blacklist Token for Logout endpoint
async def create_token_blacklist(token: str, session: AsyncSession):

    try:
        payload = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )

        exp_timestamp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp)
    except Exception:
        raise ValueError("Invalid token")
    
    token_jti = payload.get('jti') 
    session_id = payload.get('session_id')   
    blacklist_token = BlacklistedToken(token_jti=token_jti, session_id=session_id, expires_at=expires_at)

    session.add(blacklist_token)
    await session.commit()

async def get_blacklisted_token_jti(jti: str, session: AsyncSession):

    statement = select(BlacklistedToken).where(BlacklistedToken.token_jti == jti)

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def get_blacklisted_token(token: str, session: AsyncSession):

    statement = select(BlacklistedToken).where(BlacklistedToken.token == token)

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def delete_blacklisted_token(session: AsyncSession):

    now = datetime.now()

    token = delete(BlacklistedToken).where(BlacklistedToken.expires_at < now)

    await session.execute(token)
    await session.commit()


###############........Email Token
def create_url_safe_token(data: dict):
    url_serializer = URLSafeTimedSerializer(
        secret_key=Config.JWT_SECRET,
        salt="email-processing"
        )

    token = url_serializer.dumps(data)
    logging.info(f"Created token: {token}")

    return token

def decode_url_safe_token(token: str):
    url_serializer = URLSafeTimedSerializer(
        secret_key=Config.JWT_SECRET,
        salt="email-processing"
        )
    try:
        # logging.info(f"Decoding token: {token}")q
        token_data = url_serializer.loads(token)
        print("Decoded token data:", token_data)
        print("Type of token_data:", type(token_data))
        # logging.info(f"Decoded data: {token_data}")
        return token_data

    except Exception as e:
        logging.error(f"Decode failed: {e}")
        return None


def decode_password_url_safe_token(token: str, max_age: int = 300):  # 300s = 5 mins
    url_serializer = URLSafeTimedSerializer(
        secret_key=Config.JWT_SECRET,
        salt="email-processing"
    )
    try:
        return url_serializer.loads(token, max_age=max_age)

    except SignatureExpired:
        # Token valid but expired
        raise HTTPException(
            status_code=403,
            detail={"message": "Reset link has expired. Please request a new one."}
        )
    except BadSignature:
        # Token invalid or tampered
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid reset token"}
        )