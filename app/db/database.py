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


MIGRATION = "las migraciones de supabase/migrations, en orden"


async def init_db() -> None:
    """SQLite: create the tables that are missing. PostgreSQL/Supabase: the migrations create them, with RLS."""
    from app.db.models import Base

    if IS_SQLITE and settings.RENDER:
        # On Render's disk the data would vanish each time the free service sleeps: better not to start at all.
        raise RuntimeError("En Render falta DATABASE_URL: pon la cadena del Session pooler de Supabase (README, sección 18). "
                           "Con SQLite los datos se borrarían en cada reinicio.")
    async with engine.begin() as conn:
        if IS_SQLITE:
            await conn.run_sync(Base.metadata.create_all)
            # create_all never touches a table that exists: a column added in a later version is added here.
            for table, column in await conn.run_sync(_missing_columns):
                await conn.execute(text(f"alter table {table.name} add column {column.name} {column.type.compile(engine.dialect)}"))
            return
        missing = [t for t in Base.metadata.tables if (await conn.execute(text("select to_regclass(:t)"), {"t": t})).scalar() is None]
        if not missing:
            missing = [f"{table.name}.{column.name}" for table, column in await conn.run_sync(_missing_columns)]
    if missing:
        raise RuntimeError(f"Faltan tablas o columnas en la base de datos ({', '.join(missing)}). Aplica {MIGRATION} en Supabase.")


def _missing_columns(sync_conn):
    from sqlalchemy import inspect

    from app.db.models import Base

    inspector = inspect(sync_conn)
    found = []
    for table in Base.metadata.sorted_tables:
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        found += [(table, column) for column in table.columns if column.name not in existing and column.nullable]
    return found


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
