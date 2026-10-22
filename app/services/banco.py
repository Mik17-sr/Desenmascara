"""Banco de números: the community's memory of phones, Bre-B keys, accounts and links (guide section 2C)."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import mask_value
from app.db.models import Campana, Entidad, Indicador, NumeroOficial, Reporte, SolicitudRevision, Usuario, Verificacion, utcnow
from app.engine import oficiales
from app.engine.juez import BancoHit
from app.services.usuarios import value_fingerprint

RECENT_DAYS = 30
POINTS_PER_PERSON, PERSON_MAX = 6, 45
POINTS_PER_RED, RED_MAX = 2, 20
POINTS_CAMPAIGN = 15


def published_line(tipo: str, valor: str) -> oficiales.OfficialLine | None:
    """A line the entity publishes on its own website (datasets/lineas_oficiales.csv)."""
    return oficiales.official_lines().get(valor) if tipo == "telefono" else None


async def _official(session: AsyncSession, tipo: str, valor_hash: str) -> tuple[NumeroOficial, Entidad] | None:
    row = (await session.execute(
        select(NumeroOficial, Entidad).join(Entidad, Entidad.id == NumeroOficial.entidad_id)
        .where(NumeroOficial.tipo == tipo, NumeroOficial.valor_hash == valor_hash)
    )).first()
    return (row[0], row[1]) if row else None


async def _indicador(session: AsyncSession, tipo: str, valor_hash: str) -> Indicador | None:
    return await session.scalar(select(Indicador).where(Indicador.tipo == tipo, Indicador.valor_hash == valor_hash))


async def get_or_create(session: AsyncSession, tipo: str, valor: str) -> Indicador:
    valor_hash = value_fingerprint(tipo, valor)
    indicador = await _indicador(session, tipo, valor_hash)
    if indicador is None:
        indicador = Indicador(tipo=tipo, valor_hash=valor_hash, valor_visible=mask_value(valor, tipo))
        session.add(indicador)
        await session.flush()
    return indicador


async def recompute(session: AsyncSession, indicador: Indicador) -> int:
    """Risk 0-100: +6 per distinct person (max 45), +2 per red result (max 20), +15 in an active campaign.

    People who reported more than 30 days ago count half, because numbers get recycled.
    """
    now = utcnow()
    rows = await session.execute(
        select(Reporte.usuario_id, func.max(Reporte.creado_at)).where(Reporte.indicador_id == indicador.id).group_by(Reporte.usuario_id)
    )
    weighted = sum(1.0 if now - last <= timedelta(days=RECENT_DAYS) else 0.5 for _, last in rows)
    indicador.personas_distintas = (await session.scalar(
        select(func.count(func.distinct(Reporte.usuario_id))).where(Reporte.indicador_id == indicador.id)
    )) or 0
    score = min(PERSON_MAX, round(POINTS_PER_PERSON * weighted)) + min(RED_MAX, POINTS_PER_RED * indicador.consultas_rojo)
    if indicador.campana_id:
        campana = await session.get(Campana, indicador.campana_id)
        if campana and now - campana.ultimo_reporte_at <= timedelta(hours=24):
            score += POINTS_CAMPAIGN
    indicador.nivel_riesgo = min(100, score)
    return indicador.nivel_riesgo


async def report_count(session: AsyncSession, indicador: Indicador) -> int:
    return (await session.scalar(select(func.count()).select_from(Reporte).where(Reporte.indicador_id == indicador.id))) or 0


async def lookup(session: AsyncSession, tipo: str, valor: str) -> BancoHit | None:
    valor_hash = value_fingerprint(tipo, valor)
    official = await _official(session, tipo, valor_hash)
    if official:
        numero, entidad = official
        return BancoHit(tipo=tipo, visible=numero.valor_visible, nivel=0, personas=0, reportes=0, oficial_de=entidad.nombre)
    line = published_line(tipo, valor)
    if line:
        return BancoHit(tipo=tipo, visible=line.linea, nivel=0, personas=0, reportes=0, oficial_de=line.entidad, sitio=line.sitio)
    indicador = await _indicador(session, tipo, valor_hash)
    if indicador is None:
        return None
    await recompute(session, indicador)
    return BancoHit(
        tipo=tipo, visible=indicador.valor_visible, nivel=indicador.nivel_riesgo, personas=indicador.personas_distintas,
        reportes=await report_count(session, indicador), modalidad=indicador.modalidad, estado=indicador.estado,
    )


async def report(session: AsyncSession, usuario: Usuario, tipo: str, valor: str, modalidad: str | None = None,
                 verificacion_id: UUID | None = None) -> tuple[Indicador, bool]:
    """One report per person and value; reporting again only refreshes the date."""
    indicador = await get_or_create(session, tipo, valor)
    if verificacion_id and await session.get(Verificacion, verificacion_id) is None:
        verificacion_id = None  # the verification is still being saved in the background
    existing = await session.scalar(select(Reporte).where(Reporte.indicador_id == indicador.id, Reporte.usuario_id == usuario.id))
    if existing:
        existing.creado_at = utcnow()
    else:
        session.add(Reporte(indicador_id=indicador.id, usuario_id=usuario.id, verificacion_id=verificacion_id, modalidad=modalidad))
        await session.flush()
    indicador.modalidad = modalidad or indicador.modalidad
    indicador.ultimo_visto_at = utcnow()
    await recompute(session, indicador)
    return indicador, existing is None


async def add_red_result(session: AsyncSession, tipo: str, valor: str, modalidad: str | None, campana_id: UUID | None) -> None:
    """A red result that contains this value adds evidence, even before anyone reports it."""
    if published_line(tipo, valor) or await _official(session, tipo, value_fingerprint(tipo, valor)):
        return
    indicador = await get_or_create(session, tipo, valor)
    indicador.consultas_rojo += 1
    indicador.modalidad = indicador.modalidad or modalidad
    indicador.campana_id = indicador.campana_id or campana_id
    indicador.ultimo_visto_at = utcnow()
    await recompute(session, indicador)


async def request_review(session: AsyncSession, usuario: Usuario, motivo: str) -> SolicitudRevision | None:
    """Only the owner can ask: the number must be the one the person shared through Telegram."""
    if not usuario.telefono_hash:
        return None
    indicador = await _indicador(session, "telefono", usuario.telefono_hash)
    if indicador is None:
        return None
    indicador.estado = "en_revision"
    solicitud = SolicitudRevision(indicador_id=indicador.id, motivo=motivo[:300])
    session.add(solicitud)
    await session.flush()
    return solicitud


async def resolve_review(session: AsyncSession, solicitud_id: UUID, aceptar: bool) -> SolicitudRevision | None:
    solicitud = await session.get(SolicitudRevision, solicitud_id)
    if solicitud is None or solicitud.estado != "pendiente":
        return None
    indicador = await session.get(Indicador, solicitud.indicador_id)
    solicitud.estado = "aceptada" if aceptar else "rechazada"
    solicitud.resuelto_at = utcnow()
    if indicador:
        indicador.estado = "normal"
        if aceptar:  # the state diagram: an accepted review goes back to "sin reportes"
            await session.execute(delete(Reporte).where(Reporte.indicador_id == indicador.id))
            indicador.consultas_rojo = 0
            indicador.campana_id = None
            await recompute(session, indicador)
    return solicitud


async def add_official(session: AsyncSession, entidad: Entidad, tipo: str, valor: str, canal: str, fuente: str,
                       verificado_por: str) -> NumeroOficial:
    valor_hash = value_fingerprint(tipo, valor)
    existing = await session.scalar(select(NumeroOficial).where(NumeroOficial.tipo == tipo, NumeroOficial.valor_hash == valor_hash))
    if existing:
        return existing
    numero = NumeroOficial(entidad_id=entidad.id, nombre=entidad.nombre, tipo=tipo, valor_hash=valor_hash,
                           valor_visible=mask_value(valor, tipo), canal=canal, fuente=fuente, verificado_por=verificado_por)
    session.add(numero)
    await session.flush()
    return numero
