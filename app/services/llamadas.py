"""Llamada Verificada: the entity registers the call before dialing; the person asks the bot."""

import hmac
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt, encrypt, mask_value, normalize_phone
from app.db.models import Entidad, LlamadaRegistrada, Usuario, utcnow
from app.services.usuarios import value_fingerprint

CODE_TTL = timedelta(minutes=15)


async def expire(session: AsyncSession) -> None:
    """After 15 minutes the number and code are wiped; the masked row stays for the entity's panel."""
    await session.execute(
        update(LlamadaRegistrada)
        .where(LlamadaRegistrada.estado == "registrada", LlamadaRegistrada.vence_at <= utcnow())
        .values(estado="vencida", telefono_hash=None, codigo_cifrado=None)
    )


async def register(session: AsyncSession, entidad: Entidad, telefono: str, motivo: str, asesor: str) -> tuple[LlamadaRegistrada, str]:
    phone = normalize_phone(telefono)
    if phone is None:
        raise ValueError("El número del cliente no es válido.")
    code = f"{secrets.randbelow(10000):04d}"
    llamada = LlamadaRegistrada(
        entidad_id=entidad.id, telefono_hash=value_fingerprint("telefono", phone), telefono_visible=mask_value(phone, "telefono"),
        motivo=motivo.strip()[:120], asesor=asesor.strip()[:60], codigo_cifrado=encrypt(code), vence_at=utcnow() + CODE_TTL,
    )
    session.add(llamada)
    await session.flush()
    return llamada, code


async def _active_for(session: AsyncSession, usuario: Usuario, entidad: Entidad | None = None) -> list[LlamadaRegistrada]:
    await expire(session)
    if not usuario.telefono_hash:
        return []
    query = select(LlamadaRegistrada).where(
        LlamadaRegistrada.telefono_hash == usuario.telefono_hash, LlamadaRegistrada.estado == "registrada",
        LlamadaRegistrada.vence_at > utcnow(),
    )
    if entidad:
        query = query.where(LlamadaRegistrada.entidad_id == entidad.id)
    return list(await session.scalars(query.order_by(LlamadaRegistrada.creado_at.desc())))


async def consult(session: AsyncSession, usuario: Usuario, entidad: Entidad) -> tuple[LlamadaRegistrada, str] | None:
    """Only the person called can ask: the key is the number they shared through Telegram."""
    calls = await _active_for(session, usuario, entidad)
    if not calls:
        return None
    return calls[0], decrypt(calls[0].codigo_cifrado)


async def confirm(session: AsyncSession, usuario: Usuario, code: str) -> tuple[LlamadaRegistrada, Entidad] | None:
    for llamada in await _active_for(session, usuario):
        if hmac.compare_digest(decrypt(llamada.codigo_cifrado), code):
            llamada.estado = "confirmada"
            llamada.confirmada_at = utcnow()
            llamada.codigo_cifrado = None  # single use
            return llamada, await session.get(Entidad, llamada.entidad_id)
    return None


async def today(session: AsyncSession, entidad: Entidad) -> list[LlamadaRegistrada]:
    await expire(session)
    return list(await session.scalars(
        select(LlamadaRegistrada)
        .where(LlamadaRegistrada.entidad_id == entidad.id, LlamadaRegistrada.creado_at >= utcnow() - timedelta(hours=24))
        .order_by(LlamadaRegistrada.creado_at.desc())
    ))
