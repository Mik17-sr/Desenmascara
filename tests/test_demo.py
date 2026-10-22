import asyncio

from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import encrypt
from app.db.models import Base, Indicador, Reporte, Usuario
from app.services import banco, demo, entidades
from app.services.usuarios import value_fingerprint


async def _own_database():
    """A separate in-memory database, so removing the demo does not touch the other tests' data."""
    engine = create_async_engine("sqlite+aiosqlite://")
    event.listen(engine.sync_engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_demo_data_is_removed_without_touching_real_people():
    async def run():
        engine, sessions = await _own_database()
        async with sessions() as db:
            andino, _ = await entidades.create(db, "BancoAndino", "banco", "bancoandino.com", [])
            await banco.add_official(db, andino, "telefono", "576010000002", "telegram", "registro", "BancoAndino")
            await entidades.create(db, "Bancolombia", "banco", "bancolombia.com", [])
            fake = Usuario(telegram_hash=demo.user_fingerprints()[0], chat_cifrado=encrypt("0"), nombre_corto="Demo 1")
            person = Usuario(telegram_hash=value_fingerprint("telegram", "123"), chat_cifrado=encrypt("1"), nombre_corto="Demo")
            db.add_all([fake, person])
            await db.flush()
            await banco.report(db, fake, "telefono", "573000000000")      # only the demo user reported it
            shared, _ = await banco.report(db, fake, "telefono", "573100000000")
            await banco.report(db, person, "telefono", "573100000000")    # a real person reported it too
            assert await demo.present(db)

            assert await demo.remove(db) == {"entidades": 1, "usuarios": 1, "numeros": 1}
            await db.commit()
            assert not await demo.present(db)
            assert [e.nombre for e in await entidades.active(db)] == ["Bancolombia"]
            assert await db.get(Usuario, person.id) is not None             # "Demo" by name, but real
            assert await db.scalar(select(func.count()).select_from(Indicador)) == 1
            assert await db.scalar(select(func.count()).select_from(Reporte).where(Reporte.indicador_id == shared.id)) == 1
        await engine.dispose()

    asyncio.run(run())
