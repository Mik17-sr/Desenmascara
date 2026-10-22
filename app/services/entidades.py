from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_api_key, hash_password, new_api_key, new_password, password_matches
from app.db.models import AccesoEntidad, Entidad
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


async def by_id(session: AsyncSession, entity_id: str) -> Entidad | None:
    try:
        entidad = await session.get(Entidad, UUID(entity_id))
    except ValueError:
        return None
    return entidad if entidad and entidad.activa else None


async def add_access(session: AsyncSession, entidad: Entidad, correo: str) -> str:
    """Panel sign-in for an entity. Returns the generated password, shown once: only its hash is stored."""
    password = new_password()
    session.add(AccesoEntidad(entidad_id=entidad.id, correo=correo.strip().lower(), clave_hash=hash_password(password)))
    await session.flush()
    return password


async def by_login(session: AsyncSession, correo: str, clave: str) -> Entidad | None:
    acceso = await session.scalar(select(AccesoEntidad).where(AccesoEntidad.correo == correo.strip().lower()))
    if acceso is None or not password_matches(clave, acceso.clave_hash):
        return None
    return await by_id(session, str(acceso.entidad_id))


def panel_link(key: str) -> str:
    """Opens the entity panel already signed in. The key goes after '#', so it never reaches a server."""
    return f"{settings.DASHBOARD_ORIGINS.split(',')[0].strip()}/entidad#llave={key}"
