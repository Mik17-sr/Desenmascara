from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_api_key, new_api_key
from app.db.models import Entidad
from app.engine.pistas import plain


async def active(session: AsyncSession) -> list[Entidad]:
    return list(await session.scalars(select(Entidad).where(Entidad.activa.is_(True))))


async def official_domains(session: AsyncSession) -> dict[str, str]:
    return {e.nombre: e.dominio_oficial for e in await active(session) if e.dominio_oficial}


async def by_api_key(session: AsyncSession, key: str) -> Entidad | None:
    return await session.scalar(select(Entidad).where(Entidad.api_key_hash == hash_api_key(key), Entidad.activa.is_(True)))


async def by_name(session: AsyncSession, nombre: str) -> Entidad | None:
    return await session.scalar(select(Entidad).where(Entidad.nombre == nombre))


async def find_in_text(session: AsyncSession, text: str) -> Entidad | None:
    """'¿BancoAndino me está llamando?' or '¿Banco Andino me llama?' -> BancoAndino."""
    squashed = plain(text).replace(" ", "")
    for entidad in await active(session):
        if plain(entidad.nombre).replace(" ", "") in squashed:
            return entidad
    return None


async def create(session: AsyncSession, nombre: str, tipo: str, dominio: str | None, lineas: list[str]) -> tuple[Entidad, str]:
    """Returns the entity and its API key; only the key's hash is stored, so it is shown once."""
    key = new_api_key()
    entidad = Entidad(nombre=nombre, tipo=tipo, api_key_hash=hash_api_key(key), dominio_oficial=dominio, lineas_oficiales=lineas)
    session.add(entidad)
    await session.flush()
    return entidad, key
