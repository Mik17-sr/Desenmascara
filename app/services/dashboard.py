"""Aggregated, anonymous numbers for the Dashboard. It never reads a row with personal data."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Campana, Entidad, Indicador, LlamadaRegistrada, NumeroOficial, Reporte, SolicitudRevision, Verificacion, utcnow
from app.engine import oficiales as published
from app.engine.juez import MODALIDADES, risk_level
from app.services import llamadas
from app.services.usuarios import value_fingerprint

COLOMBIA = timedelta(hours=-5)
LEVEL_WORD = {"high": "Alto", "medium": "Sospechoso", "low": "Bajo"}


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() + "Z" if value else None


def _day_start() -> datetime:
    """Midnight in Colombia, expressed in UTC."""
    local = utcnow() + COLOMBIA
    return local.replace(hour=0, minute=0, second=0, microsecond=0) - COLOMBIA


async def radar(session: AsyncSession) -> dict:
    await llamadas.expire(session)
    start = _day_start()
    today = list(await session.scalars(select(Verificacion).where(Verificacion.creado_at >= start)))
    altos = [v for v in today if v.nivel == "high"]
    yesterday = (await session.scalar(select(func.count()).select_from(Verificacion).where(
        Verificacion.creado_at >= start - timedelta(days=1), Verificacion.creado_at < start))) or 0

    por_hora = [0] * 24
    for v in today:
        por_hora[(v.creado_at + COLOMBIA).hour] += 1
    tipos: dict[str, int] = {}
    for v in today:
        if v.modalidad and v.nivel in ("high", "medium"):
            name = MODALIDADES.get(v.modalidad, ("Otra",))[0]
            tipos[name] = tipos.get(name, 0) + 1

    active_since = utcnow() - timedelta(hours=24)
    campanas = list(await session.scalars(
        select(Campana).where(Campana.ultimo_reporte_at >= active_since).order_by(Campana.total_reportes.desc()).limit(5)
    ))
    hour_ago = utcnow() - timedelta(hours=1)
    alerta = None
    for c in campanas:
        last_hour = (await session.scalar(select(func.count()).select_from(Verificacion).where(
            Verificacion.campana_id == c.id, Verificacion.creado_at >= hour_ago))) or 0
        if last_hour >= 3:
            alerta = {"campana": c.nombre, "reportes_hoy": c.total_reportes, "ultima_hora": last_hour}
            break

    recientes = list(await session.scalars(select(Verificacion).order_by(Verificacion.creado_at.desc()).limit(8)))
    consultas = list(await session.scalars(
        select(Verificacion).where(Verificacion.tipo == "llamada").order_by(Verificacion.creado_at.desc()).limit(6)
    ))
    verificadas = (await session.scalar(select(func.count()).select_from(LlamadaRegistrada).where(
        LlamadaRegistrada.estado == "confirmada", LlamadaRegistrada.confirmada_at >= start))) or 0

    return {
        "actualizado": _iso(utcnow()),
        "verificaciones_hoy": len(today),
        "verificaciones_ayer": yesterday,
        "alto_riesgo_pct": round(100 * len(altos) / len(today)) if today else 0,
        "alto_riesgo_total": len(altos),
        "llamadas_reportadas": sum(1 for v in today if v.tipo in ("numero", "voz")),
        "llamadas_verificadas": verificadas,
        "campanas_activas": len(campanas),
        "tiempo_respuesta_s": round(sum(v.processing_ms for v in today) / len(today) / 1000, 1) if today else 0,
        "tipos_de_estafa": sorted(({"tipo": k, "total": n} for k, n in tipos.items()), key=lambda t: t["total"], reverse=True),
        "reportes_por_hora": [{"hora": h, "total": n} for h, n in enumerate(por_hora)],
        "campanas": [{"id": str(c.id), "nombre": c.nombre, "reportes": c.total_reportes, "ultimo": _iso(c.ultimo_reporte_at)} for c in campanas],
        "alerta": alerta,
        # Anonymous activity feed: level, score, modality, channel and time; never the text or the person.
        "actividad": [
            {"id": str(v.id)[:8], "nivel": v.nivel, "puntaje": v.puntaje, "tipo": v.tipo, "canal": v.canal,
             "modalidad": MODALIDADES.get(v.modalidad or "", (None,))[0], "cuando": _iso(v.creado_at)}
            for v in recientes
        ],
        "llamadas_ultimas": [
            {"entidad": next((s["evidence"] for s in v.senales if s["code"].startswith("LLAMADA_")), ""),
             "real": v.nivel == "low", "cuando": _iso(v.creado_at)}
            for v in consultas
        ],
    }


async def banco_view(session: AsyncSession) -> dict:
    week = utcnow() - timedelta(days=7)
    top = list(await session.scalars(
        select(Indicador).where((Indicador.personas_distintas > 0) | (Indicador.estado == "en_revision"))
        .order_by(Indicador.nivel_riesgo.desc(), Indicador.ultimo_visto_at.desc()).limit(10)
    ))
    pendientes = (await session.execute(
        select(SolicitudRevision, Indicador).join(Indicador, Indicador.id == SolicitudRevision.indicador_id)
        .where(SolicitudRevision.estado == "pendiente").order_by(SolicitudRevision.creado_at.desc())
    )).all()
    oficiales = (await session.execute(
        select(NumeroOficial, Entidad).join(Entidad, Entidad.id == NumeroOficial.entidad_id).order_by(NumeroOficial.verificado_at.desc())
    )).all()
    lines = published.official_lines()
    # An official number is never shown among the most reported, even if people reported a call that faked it.
    official_hashes = {n.valor_hash for n, _ in oficiales} | {value_fingerprint("telefono", number) for number in lines}
    top = [i for i in top if i.valor_hash not in official_hashes]
    days = []
    start = _day_start()
    for back in range(6, -1, -1):
        day = start - timedelta(days=back)
        total = (await session.scalar(select(func.count()).select_from(Reporte).where(
            Reporte.creado_at >= day, Reporte.creado_at < day + timedelta(days=1)))) or 0
        days.append({"dia": _iso(day), "total": total})
    return {
        "total": (await session.scalar(select(func.count()).select_from(Indicador))) or 0,
        "alto_riesgo": (await session.scalar(select(func.count()).select_from(Indicador).where(Indicador.nivel_riesgo >= 70))) or 0,
        "reportes_semana": (await session.scalar(select(func.count()).select_from(Reporte).where(Reporte.creado_at >= week))) or 0,
        "personas_semana": (await session.scalar(select(func.count(func.distinct(Reporte.usuario_id))).where(Reporte.creado_at >= week))) or 0,
        "oficiales": len(oficiales) + len(lines),
        "mas_reportados": [
            {"valor": i.valor_visible, "tipo": i.tipo, "personas": i.personas_distintas, "nivel": i.nivel_riesgo,
             "palabra": "En revisión" if i.estado == "en_revision" else LEVEL_WORD[risk_level(i.nivel_riesgo).value],
             "modalidad": MODALIDADES.get(i.modalidad or "", (None,))[0], "ultimo": _iso(i.ultimo_visto_at)}
            for i in top
        ],
        "solicitudes": [
            {"id": str(s.id), "valor": i.valor_visible, "motivo": s.motivo, "creado": _iso(s.creado_at)} for s, i in pendientes
        ],
        "lista_blanca": [
            {"entidad": e.nombre, "valor": n.valor_visible, "canal": n.canal, "fuente": n.fuente, "verificado_por": n.verificado_por}
            for n, e in oficiales
        ] + [
            {"entidad": line.entidad, "valor": line.linea, "canal": line.donde, "fuente": "sitio_oficial", "verificado_por": line.sitio}
            for line in lines.values()
        ],
        "reportes_por_dia": days,
    }
