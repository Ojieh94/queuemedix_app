import redis.asyncio as redis
from src.app.core.settings import Config


verify_client = redis.from_url(Config.REDIS_URL)

# --- Email verification methods ---
async def save_email_verification_token(email: str, token: str, expiry: int = 86400) -> None:
    """Saves the email verification token with a given expiry (default 24h)."""
    redis_key = f"verify:{email}"
    await verify_client.set(redis_key, token, ex=expiry)

async def get_email_verification_token(email: str) -> str | None:
    """Retrieves the verification token for an email, if it exists."""
    redis_key = f"verify:{email}"
    return await verify_client.get(redis_key)

async def delete_email_verification_token(email: str) -> None:
    """Deletes the verification token after successful verification."""
    redis_key = f"verify:{email}"
    await verify_client.delete(redis_key)