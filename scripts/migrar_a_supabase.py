"""Copy the local SQLite data (desenmascara.db) to Supabase/PostgreSQL.

    python scripts/migrar_a_supabase.py

Before: apply supabase/migrations/20261021120000_esquema_inicial.sql in Supabase and set
DATABASE_URL in .env. Keep the same HMAC_SECRET and ENCRYPTION_KEY: fingerprints and
encrypted values only work with the secrets they were made with. Tables that already have
rows in the destination are skipped, so it is safe to run twice.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.db.database import IS_SQLITE, engine as destination  # noqa: E402
from app.db.models import Base  # noqa: E402

SOURCE = f"sqlite+aiosqlite:///{ROOT / 'desenmascara.db'}"


async def main() -> None:
    if IS_SQLITE:
        raise SystemExit("DATABASE_URL apunta a SQLite. Pon la cadena de conexión de Supabase en .env.")
    source = create_async_engine(SOURCE)
    async with source.connect() as src, destination.begin() as dst:
        for table in Base.metadata.sorted_tables:  # parents before children, so foreign keys hold
            if (await dst.execute(select(func.count()).select_from(table))).scalar():
                print(f"{table.name}: ya tiene datos, se omite")
                continue
            rows = [dict(r._mapping) for r in await src.execute(select(table))]
            if rows:
                await dst.execute(table.insert(), rows)
            print(f"{table.name}: {len(rows)} filas")
    await source.dispose()
    await destination.dispose()


if __name__ == "__main__":
    asyncio.run(main())
