"""Registro trazable del caso: what happened to one check since it arrived, under its reference DSM-XXXXXXXX.

The reference is the start of the check's id, the same one printed on the result and on the kit for the police.
The trace is read from rows that already exist (the check, its campaign, the reports and the Círculo questions):
nothing extra is stored about the person.
"""

import re
from datetime import timedelta, timezone
from uuid import UUID

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AvisoCirculo, Campana, Indicador, MiembroCirculo, Reporte, Usuario, Verificacion
from app.engine.juez import MODALIDADES
from app.engine.pistas import plural
from app.services import circulo

REFERENCE = re.compile(r"(?i)\bDSM-?([0-9a-f]{8})\b")
COLOMBIA = timezone(timedelta(hours=-5))
NIVEL = {"high": "🔴 Alto riesgo", "medium": "🟡 Sospechoso", "low": "🟢 Bajo riesgo", "inconclusive": "⚪ No concluyente"}
TIPO = {"mensaje": "Mensaje", "captura": "Captura de pantalla", "voz": "Nota de voz", "numero": "Consulta de un número",
        "compra": "Compra", "llamada": "Consulta de Llamada Verificada"}
CANAL = {"telegram": "Telegram", "dashboard": "el Dashboard", "api": "la API"}
RESPUESTA = {"si": "confirmó que sí fue", "no": "confirmó que NO fue", "sin_respuesta": "no respondió en 5 minutos"}
# Círculo questions are asked while the check is analyzed, and the check is saved right after the answer: they are
# matched by time, within the same Círculo.
CIRCLE_BEFORE, CIRCLE_AFTER = timedelta(minutes=3), timedelta(minutes=20)


def reference(verificacion_id: UUID | str) -> str:
    return f"DSM-{str(verificacion_id).replace('-', '')[:8].upper()}"


def parse(text: str | None) -> str | None:
    """The 8 characters of a reference written as DSM-1A2B3C4D, dsm1a2b3c4d…"""
    found = REFERENCE.search(text or "")
    return found.group(1).lower() if found else None


def when(moment) -> str:
    local = moment.replace(tzinfo=timezone.utc).astimezone(COLOMBIA)
    return f"{local:%d/%m/%Y} {local.hour % 12 or 12}:{local:%M} {'a. m.' if local.hour < 12 else 'p. m.'}"


def _category(v: Verificacion) -> str | None:
    return MODALIDADES[v.modalidad][0] if v.modalidad in MODALIDADES else None


async def find(session: AsyncSession, ref: str, usuario: Usuario | None = None) -> Verificacion | None:
    """With a person, only their own cases: a reference is not a key to someone else's."""
    query = select(Verificacion).where(func.lower(cast(Verificacion.id, String)).like(f"{ref.lower()}%"))
    if usuario is not None:
        query = query.where(Verificacion.usuario_id == usuario.id)
    return await session.scalar(query.order_by(Verificacion.creado_at.desc()).limit(1))


async def recent(session: AsyncSession, usuario: Usuario, limit: int = 5) -> list[dict]:
    rows = await session.scalars(select(Verificacion).where(Verificacion.usuario_id == usuario.id)
                                 .order_by(Verificacion.creado_at.desc()).limit(limit))
    return [{"referencia": reference(v.id), "cuando": when(v.creado_at), "nivel": v.nivel, "categoria": _category(v),
             "tipo": TIPO.get(v.tipo, "Mensaje")} for v in rows]


async def trace(session: AsyncSession, v: Verificacion, names: bool = True) -> dict:
    """Every step of the case, oldest first. names=False for the team: relatives appear as «un familiar»."""
    at = when(v.creado_at)
    analysis = f"{NIVEL.get(v.nivel, v.nivel)} · {v.puntaje}/100" + (f" · {_category(v)}" if _category(v) else "")
    if v.processing_ms:
        analysis += f" · en {v.processing_ms / 1000:.1f} s".replace(".", ",")
    events = [{"cuando": at, "paso": "Recibido", "detalle": f"{TIPO.get(v.tipo, 'Mensaje')} por {CANAL.get(v.canal, v.canal)}."},
              {"cuando": at, "paso": "Analizado", "detalle": analysis + "."}]
    estado = "Analizado"

    if v.campana_id and (campana := await session.get(Campana, v.campana_id)):
        who = "identificada por el equipo de Desenmascara" if campana.regla else "detectada automáticamente"
        events.append({"cuando": at, "paso": "Parte de una campaña",
                       "detalle": f"«{campana.nombre}», {who}: {plural(campana.total_reportes, 'reporte', 'reportes')} desde el "
                                  f"{when(campana.primer_reporte_at).split(' ')[0]}."})
        estado = "En seguimiento: parte de una campaña"

    owner = await session.get(Usuario, v.usuario_id) if v.usuario_id else None
    own = await circulo.own_circle(session, owner) if owner else None
    if own:
        rows = await session.execute(
            select(AvisoCirculo, MiembroCirculo).join(MiembroCirculo, MiembroCirculo.id == AvisoCirculo.destinatario_id)
            .where(AvisoCirculo.circulo_id == own.id, AvisoCirculo.creado_at >= v.creado_at - CIRCLE_BEFORE,
                   AvisoCirculo.creado_at <= v.creado_at + CIRCLE_AFTER).order_by(AvisoCirculo.creado_at))
        avisos = list(rows)
        for aviso, miembro in (a for a in avisos if a[0].tipo == "pregunta"):
            name = miembro.nombre if names else "un familiar"
            answer = RESPUESTA.get(aviso.respuesta, "todavía no responde")
            events.append({"cuando": when(aviso.creado_at), "paso": "Círculo de Confianza",
                           "detalle": f"Se le preguntó a {name} si había escrito: {answer}."})
            estado = "Confirmado por el Círculo: es una estafa" if aviso.respuesta == "no" else estado
        alerts = [a for a, _ in avisos if a.tipo == "alerta"]
        if alerts:
            events.append({"cuando": when(alerts[0].creado_at), "paso": "Aviso al Círculo",
                           "detalle": f"Se avisó a {plural(len(alerts), 'familiar', 'familiares')} para que no cayeran."})

    reports = (await session.execute(select(Reporte, Indicador).join(Indicador, Indicador.id == Reporte.indicador_id)
                                     .where(Reporte.verificacion_id == v.id).order_by(Reporte.creado_at))).all()
    if reports:
        values = ", ".join(i.valor_visible for _, i in reports[:4])
        events.append({"cuando": when(reports[0][0].creado_at), "paso": "Reportado al Banco de números",
                       "detalle": f"{values}. La próxima persona que lo consulte recibe el aviso."})
        estado = "Reportado al Banco de números" + (" · parte de una campaña" if v.campana_id else "")
    return {"referencia": reference(v.id), "estado": estado, "nivel": v.nivel, "categoria": _category(v), "eventos": events}
