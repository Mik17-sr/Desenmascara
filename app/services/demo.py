"""The demo data that scripts/seed_demo.py loads, so it can be shown as such and removed before a delivery.

Demo users are recognised by their exact fingerprint ("demo-1" … "demo-30"), never by name, so a
real person called "Demo" is never touched.
"""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Campana, Entidad, Indicador, LlamadaRegistrada, Reporte, SolicitudRevision, Usuario, Verificacion,
)
from app.services import banco
from app.services.usuarios import value_fingerprint

ENTIDADES = ("BancoAndino", "Tienda Ejemplo")
USUARIOS = 30


def user_fingerprints() -> list[str]:
    return [value_fingerprint("telegram", f"demo-{i}") for i in range(1, USUARIOS + 1)]


async def present(session: AsyncSession) -> bool:
    entities = await session.scalar(select(func.count()).select_from(Entidad).where(Entidad.nombre.in_(ENTIDADES)))
    users = await session.scalar(select(func.count()).select_from(Usuario).where(Usuario.telegram_hash.in_(user_fingerprints())))
    return bool(entities or users)


async def remove(session: AsyncSession) -> dict[str, int]:
    """Fictional entities (their calls and official numbers go with them) and demo users with their reports."""
    entities = (await session.scalars(select(Entidad).where(Entidad.nombre.in_(ENTIDADES)))).all()
    users = (await session.scalars(select(Usuario).where(Usuario.telegram_hash.in_(user_fingerprints())))).all()
    touched = set(await session.scalars(select(Reporte.indicador_id).where(Reporte.usuario_id.in_([u.id for u in users]))))
    for row in (*entities, *users):
        await session.delete(row)
    await session.flush()
    emptied = 0
    for indicador in (await session.scalars(select(Indicador).where(Indicador.id.in_(touched)))).all():
        if await session.scalar(select(func.count()).select_from(Reporte).where(Reporte.indicador_id == indicador.id)):
            await banco.recompute(session, indicador)  # real people reported it too: keep it with their reports
        else:
            await session.delete(indicador)
            emptied += 1
    return {"entidades": len(entities), "usuarios": len(users), "numeros": emptied}


async def remove_activity(session: AsyncSession) -> dict[str, int]:
    """Every check, campaign, report and call, to start a delivery from zero. Users, their Círculos and
    the real entities stay."""
    counts = {}
    for name, model in (("verificaciones", Verificacion), ("campanas", Campana), ("reportes", Reporte),
                        ("solicitudes", SolicitudRevision), ("numeros", Indicador), ("llamadas", LlamadaRegistrada)):
        counts[name] = (await session.execute(delete(model))).rowcount or 0
    return counts
