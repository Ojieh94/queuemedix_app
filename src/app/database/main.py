from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from src.app.core.settings import Config

# Create the async engine properly
async_engine = create_async_engine(
    Config.DATABASE_URL,
    echo=False  # Optional: Set to True for SQL logging
)

# Create a sessionmaker factory for reuse
async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Initialize the database (e.g. on app startup)
async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependency or function to get a session
async def get_session():
    async with async_session_factory() as session:
        yield session
