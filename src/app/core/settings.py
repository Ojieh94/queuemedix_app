from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    

    model_config = SettingsConfigDict(extra="ignore")

@lru_cache
def get_settings():
    return Settings()

Config = get_settings()

broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL
broker_connection_retry_on_startup = True
