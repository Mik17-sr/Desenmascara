from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./desenmascara.db"


def _async_database_url() -> str:
    url = settings.DATABASE_URL or settings.SUPABASE_DB_URL or DEFAULT_SQLITE_URL
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_database_url = _async_database_url()
IS_SQLITE = _database_url.startswith("sqlite")
if not IS_SQLITE and "prepared_statement_cache_size" not in _database_url:
    # Supabase's pooler (PgBouncer) does not keep prepared statements between transactions.
    _database_url += ("&" if "?" in _database_url else "?") + "prepared_statement_cache_size=0"
engine = create_async_engine(
    _database_url, pool_pre_ping=True, connect_args={} if IS_SQLITE else {"statement_cache_size": 0},
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

if IS_SQLITE:
    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        # WAL lets the dashboard read while the API writes; SQLite needs foreign keys turned on.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


MIGRATION = "supabase/migrations/20261021120000_esquema_inicial.sql"


async def init_db() -> None:
    """SQLite: create the 12 tables. PostgreSQL/Supabase: the migration creates them, with RLS."""
    from app.db.models import Base

    async with engine.begin() as conn:
        if IS_SQLITE:
            await conn.run_sync(Base.metadata.create_all)
            return
        missing = [t for t in Base.metadata.tables if (await conn.execute(text("select to_regclass(:t)"), {"t": t})).scalar() is None]
    if missing:
        raise RuntimeError(f"Faltan tablas en la base de datos ({', '.join(missing)}). Aplica {MIGRATION} en Supabase.")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
