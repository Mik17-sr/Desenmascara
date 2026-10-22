"""Círculo de Confianza: double consent, '¿fuiste tú?' questions and chain alerts.

On Telegram a bot cannot write first, so the protected person sends the relative an invite
link; opening it is the relative's consent and lets the bot write to them later.

Validating the relative, so that a forwarded or stolen link is not enough to join:
1. the protected person gives the relative's number with the invitation (the link lasts 48 h, once);
2. whoever accepts shares their own number through Telegram's button, and it must be that one;
3. if the protected person set a pregunta de confidencialidad, they answer it (three tries);
4. the protected person confirms "¿es tu familiar?"; only then is the relative in the Círculo.
"""

import re
import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AvisoCirculo, Circulo, MiembroCirculo, Usuario, utcnow
from app.engine.pistas import plain
from app.core.security import decrypt, encrypt, normalize_phone
from app.services.usuarios import set_phone, value_fingerprint

INVITE_HOURS = 48
ANSWER_TRIES = 3


def normalize_answer(text: str) -> str:
    """'Firulais', ' firuláis.' and 'FIRULAIS' are the same answer."""
    return " ".join(re.findall(r"[a-z0-9ñ]+", plain(text)))


def question_of(miembro: MiembroCirculo) -> str | None:
    return decrypt(miembro.pregunta_cifrada) if miembro.pregunta_cifrada else None


async def own_circle(session: AsyncSession, protegido: Usuario) -> Circulo | None:
    return await session.scalar(
        select(Circulo).join(MiembroCirculo, MiembroCirculo.circulo_id == Circulo.id)
        .where(MiembroCirculo.usuario_id == protegido.id, MiembroCirculo.rol == "protegido")
    )


async def invite(session: AsyncSession, protegido: Usuario, nombre: str, telefono: str, relacion: str | None = None,
                 pregunta: str | None = None, respuesta: str | None = None) -> str:
    """ValueError when the number is not valid or is the protected person's own, or the question has no answer."""
    phone = normalize_phone(telefono)
    if phone is None:
        raise ValueError("No reconocí ese número.")
    phone_hash = value_fingerprint("telefono", phone)
    if phone_hash == protegido.telefono_hash:
        raise ValueError("Ese es tu propio número: escribe el de tu familiar.")
    pregunta = (pregunta or "").strip() or None
    if bool(pregunta) != bool(respuesta and normalize_answer(respuesta)):
        raise ValueError("La pregunta de confidencialidad necesita su respuesta.")
    circulo = await own_circle(session, protegido)
    if circulo is None:
        circulo = Circulo(nombre=f"Círculo de {protegido.nombre_corto or 'mi familia'}")
        session.add(circulo)
        await session.flush()
        session.add(MiembroCirculo(circulo_id=circulo.id, usuario_id=protegido.id, rol="protegido",
                                   nombre=protegido.nombre_corto or "Protegido", acepto_at=utcnow()))
    token = secrets.token_urlsafe(12)
    session.add(MiembroCirculo(circulo_id=circulo.id, rol="familiar", nombre=nombre.strip()[:60], relacion=relacion,
                               invitacion_hash=value_fingerprint("invitacion", token), telefono_hash=phone_hash,
                               pregunta_cifrada=encrypt(pregunta[:160]) if pregunta else None,
                               respuesta_hash=value_fingerprint("respuesta", normalize_answer(respuesta)) if pregunta else None,
                               intentos=0))
    await session.flush()
    return token


def _expired(miembro: MiembroCirculo) -> bool:
    return miembro.creado_at < utcnow() - timedelta(hours=INVITE_HOURS)


async def pending_invite(session: AsyncSession, token: str) -> tuple[MiembroCirculo, Usuario] | None:
    """None when the link does not exist, was used or is older than 48 hours."""
    miembro = await session.scalar(select(MiembroCirculo).where(MiembroCirculo.invitacion_hash == value_fingerprint("invitacion", token)))
    if miembro is None or _expired(miembro):
        return None
    protegido = await session.scalar(
        select(Usuario).join(MiembroCirculo, MiembroCirculo.usuario_id == Usuario.id)
        .where(MiembroCirculo.circulo_id == miembro.circulo_id, MiembroCirculo.rol == "protegido")
    )
    return miembro, protegido


async def accept(session: AsyncSession, token: str, familiar: Usuario, acepta: bool,
                 telefono: str | None = None) -> tuple[str, MiembroCirculo, Usuario] | None:
    """(estado, member, protected person). estado: rechazada, pregunta (the number matched: now the pregunta de
    confidencialidad), por_aprobar (the number matched and there is no question: the protected person confirms next),
    no_coincide (another number: the link keeps waiting for the real relative) or sin_numero (an invitation from
    before the validation). The number is the one Telegram's contact button gave the bot."""
    found = await pending_invite(session, token)
    if found is None or found[1].id == familiar.id:
        return None
    miembro, protegido = found
    if not acepta:
        await session.delete(miembro)
        return "rechazada", miembro, protegido
    if miembro.telefono_hash is None:
        return "sin_numero", miembro, protegido
    phone = normalize_phone(telefono or "")
    if phone is None or value_fingerprint("telefono", phone) != miembro.telefono_hash:
        return "no_coincide", miembro, protegido
    await set_phone(session, familiar, phone)
    miembro.usuario_id = familiar.id
    miembro.invitacion_hash = None  # one use
    return ("pregunta" if miembro.respuesta_hash else "por_aprobar"), miembro, protegido


async def answer_question(session: AsyncSession, familiar: Usuario, miembro_id: UUID,
                          respuesta: str) -> tuple[str, MiembroCirculo, Usuario, int] | None:
    """The relative answers the pregunta de confidencialidad. (estado, member, protected person, tries left):
    correcta (the protected person confirms next), incorrecta, or bloqueada (third wrong answer: the invitation is
    cancelled). None unless this relative is the one waiting for that question."""
    miembro = await session.get(MiembroCirculo, miembro_id)
    if miembro is None or miembro.usuario_id != familiar.id or miembro.acepto_at is not None or not miembro.respuesta_hash:
        return None
    protegido = await session.scalar(
        select(Usuario).join(MiembroCirculo, MiembroCirculo.usuario_id == Usuario.id)
        .where(MiembroCirculo.circulo_id == miembro.circulo_id, MiembroCirculo.rol == "protegido")
    )
    if value_fingerprint("respuesta", normalize_answer(respuesta)) == miembro.respuesta_hash:
        miembro.respuesta_hash = None  # answered: now it waits for the protected person's "sí"
        miembro.intentos = 0
        return "correcta", miembro, protegido, ANSWER_TRIES
    miembro.intentos = (miembro.intentos or 0) + 1
    left = ANSWER_TRIES - miembro.intentos
    if left <= 0:
        await session.delete(miembro)
        return "bloqueada", miembro, protegido, 0
    return "incorrecta", miembro, protegido, left


async def approve(session: AsyncSession, protegido: Usuario, miembro_id: UUID, aprueba: bool) -> tuple[MiembroCirculo, Usuario] | None:
    """The protected person's answer to "¿es tu familiar?". None unless it is their own Círculo and the relative is
    waiting for it."""
    miembro = await session.get(MiembroCirculo, miembro_id)
    circulo = await own_circle(session, protegido)
    if miembro is None or circulo is None or miembro.circulo_id != circulo.id or miembro.rol != "familiar" \
            or miembro.usuario_id is None or miembro.acepto_at is not None:
        return None
    familiar = await session.get(Usuario, miembro.usuario_id)
    if aprueba:
        miembro.acepto_at = utcnow()
    else:
        await session.delete(miembro)
    return miembro, familiar


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
    invited = await session.scalars(select(MiembroCirculo).where(
        MiembroCirculo.circulo_id == circulo.id, MiembroCirculo.usuario_id.is_(None), MiembroCirculo.acepto_at.is_(None)))
    answering = await session.scalars(select(MiembroCirculo).where(
        MiembroCirculo.circulo_id == circulo.id, MiembroCirculo.usuario_id.is_not(None), MiembroCirculo.acepto_at.is_(None),
        MiembroCirculo.respuesta_hash.is_not(None)))
    return [m.nombre for m in invited if not _expired(m)] + [f"{m.nombre} (falta la pregunta)" for m in answering]


async def to_approve(session: AsyncSession, protegido: Usuario) -> list[MiembroCirculo]:
    """Relatives whose number matched, who answered the question if there was one, and wait for the protected person's "sí"."""
    circulo = await own_circle(session, protegido)
    if circulo is None:
        return []
    return list(await session.scalars(select(MiembroCirculo).where(
        MiembroCirculo.circulo_id == circulo.id, MiembroCirculo.rol == "familiar", MiembroCirculo.usuario_id.is_not(None),
        MiembroCirculo.acepto_at.is_(None), MiembroCirculo.respuesta_hash.is_(None))))


def mentioned(text: str, candidates: list[tuple[MiembroCirculo, Usuario]]) -> list[tuple[MiembroCirculo, Usuario]]:
    words = set(re.findall(r"\w+", plain(text)))
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
