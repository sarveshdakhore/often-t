from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Add alias for backward compatibility with newer code
async_session_maker = AsyncSessionLocal

# Base class for declarative models
Base = declarative_base()

from typing import AsyncGenerator

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    async with AsyncSessionLocal() as session:
        yield session
