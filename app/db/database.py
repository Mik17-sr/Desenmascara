from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _async_database_url() -> Optional[str]:
    url = settings.DATABASE_URL or settings.SUPABASE_DB_URL
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_database_url = _async_database_url()
engine = create_async_engine(_database_url, pool_pre_ping=True) if _database_url else None
SessionLocal = (
    async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    if engine
    else None
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        raise RuntimeError("Database is not configured")
    async with SessionLocal() as session:
        yield session
