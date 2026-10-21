"""Círculo de Confianza: double consent, '¿fuiste tú?' questions and chain alerts.

On Telegram a bot cannot write first, so the protected person sends the relative an invite
link; opening it is the relative's consent and lets the bot write to them later.
"""

import secrets
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AvisoCirculo, Circulo, MiembroCirculo, Usuario, utcnow
from app.engine.pistas import plain
from app.services.usuarios import value_fingerprint


async def own_circle(session: AsyncSession, protegido: Usuario) -> Circulo | None:
    return await session.scalar(
        select(Circulo).join(MiembroCirculo, MiembroCirculo.circulo_id == Circulo.id)
        .where(MiembroCirculo.usuario_id == protegido.id, MiembroCirculo.rol == "protegido")
    )


async def invite(session: AsyncSession, protegido: Usuario, nombre: str, relacion: str | None = None) -> str:
    circulo = await own_circle(session, protegido)
    if circulo is None:
        circulo = Circulo(nombre=f"Círculo de {protegido.nombre_corto or 'mi familia'}")
        session.add(circulo)
        await session.flush()
        session.add(MiembroCirculo(circulo_id=circulo.id, usuario_id=protegido.id, rol="protegido",
                                   nombre=protegido.nombre_corto or "Protegido", acepto_at=utcnow()))
    token = secrets.token_urlsafe(12)
    session.add(MiembroCirculo(circulo_id=circulo.id, rol="familiar", nombre=nombre.strip()[:60], relacion=relacion,
                               invitacion_hash=value_fingerprint("invitacion", token)))
    await session.flush()
    return token


async def pending_invite(session: AsyncSession, token: str) -> tuple[MiembroCirculo, Usuario] | None:
    miembro = await session.scalar(select(MiembroCirculo).where(MiembroCirculo.invitacion_hash == value_fingerprint("invitacion", token)))
    if miembro is None:
        return None
    protegido = await session.scalar(
        select(Usuario).join(MiembroCirculo, MiembroCirculo.usuario_id == Usuario.id)
        .where(MiembroCirculo.circulo_id == miembro.circulo_id, MiembroCirculo.rol == "protegido")
    )
    return miembro, protegido


async def accept(session: AsyncSession, token: str, familiar: Usuario, acepta: bool) -> tuple[MiembroCirculo, Usuario] | None:
    found = await pending_invite(session, token)
    if found is None or found[1].id == familiar.id:
        return None
    miembro, protegido = found
    if acepta:
        miembro.usuario_id = familiar.id
        miembro.acepto_at = utcnow()
        miembro.invitacion_hash = None
    else:
        await session.delete(miembro)
    return miembro, protegido


async def members(session: AsyncSession, protegido: Usuario) -> list[tuple[MiembroCirculo, Usuario]]:
    circulo = await own_circle(session, protegido)
    if circulo is None:
        return []
    rows = await session.execute(
        select(MiembroCirculo, Usuario).join(Usuario, Usuario.id == MiembroCirculo.usuario_id)
        .where(MiembroCirculo.circulo_id == circulo.id, MiembroCirculo.rol == "familiar", MiembroCirculo.acepto_at.is_not(None))
    )
    return [(m, u) for m, u in rows]


async def pending_names(session: AsyncSession, protegido: Usuario) -> list[str]:
    circulo = await own_circle(session, protegido)
    if circulo is None:
        return []
    return list(await session.scalars(
        select(MiembroCirculo.nombre).where(MiembroCirculo.circulo_id == circulo.id, MiembroCirculo.acepto_at.is_(None))
    ))


def mentioned(text: str, candidates: list[tuple[MiembroCirculo, Usuario]]) -> list[tuple[MiembroCirculo, Usuario]]:
    words = set(plain(text).replace(",", " ").split())
    return [(m, u) for m, u in candidates if plain(m.nombre).split()[0] in words]


async def ask(session: AsyncSession, protegido: Usuario, text: str, verificacion_id: UUID | None,
              sender: Usuario | None = None) -> list[tuple[AvisoCirculo, MiembroCirculo, Usuario]]:
    """Ask the relative the message claims to be. If it came from that relative's own account
    (a stolen account), ask someone else in the Círculo instead."""
    candidates = await members(session, protegido)
    targets = mentioned(text, candidates) or candidates
    if sender is not None:
        targets = [(m, u) for m, u in targets if u.id != sender.id] or [(m, u) for m, u in candidates if u.id != sender.id]
    circulo = await own_circle(session, protegido)
    avisos = []
    for miembro, usuario in targets:
        aviso = AvisoCirculo(circulo_id=circulo.id, destinatario_id=miembro.id, verificacion_id=None, tipo="pregunta")
        session.add(aviso)
        avisos.append((aviso, miembro, usuario))
    await session.flush()
    return avisos


async def answer(session: AsyncSession, aviso_id: UUID, familiar: Usuario, respuesta: str):
    """Returns (aviso, member who answered, protected person, the other members) or None."""
    aviso = await session.get(AvisoCirculo, aviso_id)
    if aviso is None or aviso.respuesta is not None:
        return None
    miembro = await session.get(MiembroCirculo, aviso.destinatario_id)
    if miembro is None or miembro.usuario_id != familiar.id:
        return None
    aviso.respuesta = respuesta
    aviso.respondido_at = utcnow()
    protegido = await session.scalar(
        select(Usuario).join(MiembroCirculo, MiembroCirculo.usuario_id == Usuario.id)
        .where(MiembroCirculo.circulo_id == aviso.circulo_id, MiembroCirculo.rol == "protegido")
    )
    others = [(m, u) for m, u in await members(session, protegido) if u.id != familiar.id]
    return aviso, miembro, protegido, others


async def expire_question(session: AsyncSession, aviso_id: UUID) -> AvisoCirculo | None:
    """Five minutes without an answer: 'no pudimos confirmarlo'. None if someone already answered."""
    aviso = await session.get(AvisoCirculo, aviso_id)
    if aviso is None or aviso.respuesta is not None:
        return None
    aviso.respuesta = "sin_respuesta"
    aviso.respondido_at = utcnow()
    return aviso


async def alert_all(session: AsyncSession, protegido: Usuario, tipo: str = "alerta") -> list[Usuario]:
    circulo = await own_circle(session, protegido)
    targets = await members(session, protegido)
    for miembro, _ in targets:
        session.add(AvisoCirculo(circulo_id=circulo.id, destinatario_id=miembro.id, tipo=tipo))
    return [u for _, u in targets]


async def leave(session: AsyncSession, usuario: Usuario) -> int:
    """Anyone can leave with one message: as a relative, or by deleting their own Círculo."""
    own = await own_circle(session, usuario)
    if own:
        await session.execute(delete(Circulo).where(Circulo.id == own.id))
    result = await session.execute(delete(MiembroCirculo).where(MiembroCirculo.usuario_id == usuario.id, MiembroCirculo.rol == "familiar"))
    return (result.rowcount or 0) + (1 if own else 0)
