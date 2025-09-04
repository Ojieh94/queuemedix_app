import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


env = os.getenv("ENV", "local")

if env == "local":
    env_file = ".env.local"

else:
    env_file = ".env.docker"


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    EMAIL_SERVER: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str
    MAIL_FROM_NAME: str
    REDIS_URL: str
    DOMAIN: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int

    model_config=SettingsConfigDict(
        env_file=env_file,
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()

Config = get_settings()

broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL
broker_connection_retry_on_startup =True