import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from api.models import Base
from api.config import settings


# Database configuration
try:
    DATABASE_URL = settings.database_url
except:
    # Fallback if settings fail
    DATABASE_URL = "sqlite:///:memory:"

# Convert database URLs for async drivers
if DATABASE_URL.startswith("sqlite"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine with appropriate settings
engine_kwargs = {
    "echo": False,
    "future": True,
}

# Add pool settings for PostgreSQL
if "postgresql" in DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })
elif "sqlite" in DATABASE_URL and ":memory:" in DATABASE_URL:
    # Special handling for in-memory SQLite
    engine_kwargs.update({
        "pool_pre_ping": False,
        "poolclass": None,  # Disable pooling for in-memory
    })
elif "sqlite" in DATABASE_URL:
    engine_kwargs["pool_pre_ping"] = True

engine: AsyncEngine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    """Get the database engine."""
    return engine


@asynccontextmanager
async def get_db_session():
    """Create and manage database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    # Ensure data directory exists if using SQLite
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.split("///")[-1]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables (useful for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_db():
    """Dependency to get database session for FastAPI routes."""
    async with get_db_session() as session:
        yield session
