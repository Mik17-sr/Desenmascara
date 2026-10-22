"""History of checks and campaign memory (revisión 5, el archivista)."""

import logging
import re
from collections import Counter
from datetime import timedelta
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import SessionLocal
from app.db.models import Campana, Verificacion, utcnow
from app.engine import archivista
from app.engine.enlaces import registered_domain
from app.engine.juez import MODALIDADES, CampaignHit
from app.engine.pistas import CUENTA_PATTERN, PHONE_PATTERN, Pistas
from app.schemas.contract import AnalysisResult, LinkStatus, RiskLevel
from app.services import banco

logger = logging.getLogger(__name__)

SIMILAR = 0.6
LOOKBACK = timedelta(days=7)
# A campaign the team identified (regla) is matched with no time limit; a detected one does the same once this many
# reports joined it, so the rules grow from what the API registers by itself.
REGLA_AUTOMATICA = 5
TENDENCIA_MIN = 3  # cases of one modalidad in 7 days for the bot to say it is spreading
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
NAME_AFTER = re.compile(r"(?i)\b(soy|me llamo|habla|le habla|mi nombre es)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)")
# Long digit runs (IDs, accounts) go; an amount after "$" stays: it is not personal, and the Dashboard adds up
# what scams ask for.
LONG_NUMBER = re.compile(r"(?<!\$)(?<!\$ )\b\d[\d .-]{5,}\d\b")


def anonymize(text: str) -> str:
    """Remove names, phones, IDs and accounts before storing (guide section 16)."""
    text = EMAIL_PATTERN.sub("[correo]", text)
    text = PHONE_PATTERN.sub("[número]", text)
    text = CUENTA_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[cuenta]"), text)
    text = LONG_NUMBER.sub("[número]", text)
    return NAME_AFTER.sub(lambda m: f"{m.group(1)} [nombre]", text)[:2000]


async def _similar_recent(session: AsyncSession, huella: list[int] | None) -> list[tuple[Verificacion, float]]:
    if not huella:
        return []
    rows = await session.scalars(
        select(Verificacion)
        .where(Verificacion.creado_at >= utcnow() - LOOKBACK, Verificacion.huella.is_not(None),
               Verificacion.nivel.in_([RiskLevel.HIGH.value, RiskLevel.MEDIUM.value]))
        .order_by(Verificacion.creado_at.desc()).limit(2000)
    )
    matches = [(v, archivista.similarity(huella, v.huella)) for v in rows]
    return sorted((m for m in matches if m[1] >= SIMILAR), key=lambda m: m[1], reverse=True)


async def rule_campaigns(session: AsyncSession) -> list[Campana]:
    return list(await session.scalars(
        select(Campana).where(Campana.estado == "activa", or_(Campana.regla.is_(True), Campana.total_reportes >= REGLA_AUTOMATICA))
        .order_by(Campana.ultimo_reporte_at.desc()).limit(300)))


async def _rule_match(session: AsyncSession, huella: list[int] | None) -> tuple[Campana, float] | None:
    """The closest rule campaign; one identified by the team wins over a detected one."""
    if not huella:
        return None
    best = None
    for campana in await rule_campaigns(session):
        sim = archivista.similarity(huella, campana.centroide)
        if sim >= SIMILAR and (best is None or (bool(campana.regla), sim) > (bool(best[0].regla), best[1])):
            best = (campana, sim)
    return best


async def best_campaign(session: AsyncSession, huella: list[int] | None) -> CampaignHit | None:
    matches = await _similar_recent(session, huella)
    rule = await _rule_match(session, huella)
    today = utcnow() - timedelta(hours=24)
    if rule:
        campana, sim = rule
        return CampaignHit(id=str(campana.id), nombre=campana.nombre, similitud=max(sim, matches[0][1] if matches else 0.0),
                           reportes_hoy=sum(1 for v, _ in matches if v.creado_at >= today), descripcion=campana.descripcion,
                           total=campana.total_reportes, confirmada=bool(campana.regla), modalidad=campana.modalidad)
    if not matches:
        return None
    campaign_ids = Counter(v.campana_id for v, _ in matches if v.campana_id)
    nombre, campaign_id = "Mensajes parecidos", ""
    if campaign_ids:
        campana = await session.get(Campana, campaign_ids.most_common(1)[0][0])
        nombre, campaign_id = campana.nombre, str(campana.id)
    reportes_hoy = sum(1 for v, _ in matches if v.creado_at >= today)
    return CampaignHit(id=campaign_id, nombre=nombre, similitud=matches[0][1], reportes_hoy=max(1, reportes_hoy))


def _campaign_name(pistas: Pistas, modalidad: str | None, text: str) -> str:
    who = pistas.entidades[0] if pistas.entidades else MODALIDADES.get(modalidad or "", ("Campaña",))[0]
    words = re.findall(r"[\wáéíóúñÁÉÍÓÚÑ$.]+", anonymize(text))
    snippet = " ".join(w for w in words if w.lower() not in who.lower())[:48].strip()
    return f"Falso {who} · «{snippet}…»" if pistas.entidades else f"{who} · «{snippet}…»"


async def save(verificacion_id: UUID, *, usuario_id: UUID | None, canal: str, tipo: str, text: str, result: AnalysisResult,
               huella: list[int] | None, pistas: Pistas, llamada_id: UUID | None = None) -> None:
    """Runs after the answer is sent: a slow database never delays the person."""
    try:
        async with SessionLocal() as session:
            await _save(session, verificacion_id, usuario_id=usuario_id, canal=canal, tipo=tipo, text=text,
                        result=result, huella=huella, pistas=pistas, llamada_id=llamada_id)
            await session.commit()
    except Exception:
        # Persistence is best-effort; do not expose database errors or affect analysis.
        logger.warning("Analysis persistence unavailable", exc_info=True)


async def _save(session: AsyncSession, verificacion_id: UUID, *, usuario_id, canal, tipo, text, result, huella, pistas, llamada_id) -> None:
    risky = result.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
    campana = None
    if risky and huella:
        matches = await _similar_recent(session, huella)
        joined = next((v.campana_id for v, _ in matches if v.campana_id), None)
        if joined is None and (rule := await _rule_match(session, huella)):
            joined = rule[0].id  # a rule campaign older than the 7-day window
        if joined:
            campana = await session.get(Campana, joined)
        elif matches and result.risk_level == RiskLevel.HIGH:
            campana = Campana(nombre=_campaign_name(pistas, result.modalidad, text), modalidad=result.modalidad,
                              centroide=huella, total_reportes=len(matches))
            session.add(campana)
            await session.flush()
            for v, _ in matches:
                v.campana_id = campana.id
        if campana:
            campana.total_reportes += 1
            campana.ultimo_reporte_at = utcnow()
            campana.estado = "activa"

    session.add(Verificacion(
        id=verificacion_id, usuario_id=usuario_id, campana_id=campana.id if campana else None, llamada_id=llamada_id,
        canal=canal, tipo=tipo, texto_anonimizado=anonymize(text), puntaje=result.risk_score, nivel=result.risk_level.value,
        modalidad=result.modalidad, senales=[s.model_dump(mode="json") for s in result.signals], huella=huella,
        processing_ms=result.processing_ms,
    ))
    if result.risk_level == RiskLevel.HIGH:
        campana_id = campana.id if campana else None
        for tipo_valor, valores in (("telefono", pistas.telefonos), ("llave", pistas.llaves), ("cuenta", pistas.cuentas)):
            for valor in valores[:3]:
                await banco.add_red_result(session, tipo_valor, valor, result.modalidad, campana_id)
        for link in result.links:
            if link.status != LinkStatus.OFFICIAL:
                domain = registered_domain(urlsplit(link.url).hostname or "")
                await banco.add_red_result(session, "enlace", domain, result.modalidad, campana_id)


async def modality_this_week(session: AsyncSession, modalidad: str) -> int:
    """Risky checks of this modalidad in the last 7 days, the one being answered included."""
    saved = await session.scalar(select(func.count()).select_from(Verificacion).where(
        Verificacion.modalidad == modalidad, Verificacion.creado_at >= utcnow() - LOOKBACK,
        Verificacion.nivel.in_([RiskLevel.HIGH.value, RiskLevel.MEDIUM.value])))
    return (saved or 0) + 1


# --- Campaigns for the team: identify, describe and turn into rules ---------------------------

async def campaigns_for_review(session: AsyncSession, limit: int = 40) -> list[dict]:
    rows = await session.scalars(select(Campana).order_by(Campana.regla.desc(), Campana.ultimo_reporte_at.desc()).limit(limit))
    out = []
    for c in rows:
        example = await session.scalar(select(Verificacion.texto_anonimizado).where(Verificacion.campana_id == c.id)
                                       .order_by(Verificacion.creado_at.desc()).limit(1))
        out.append({"id": str(c.id), "nombre": c.nombre, "modalidad": c.modalidad, "reportes": c.total_reportes, "estado": c.estado,
                    "regla": bool(c.regla), "regla_automatica": not c.regla and c.total_reportes >= REGLA_AUTOMATICA,
                    "descripcion": c.descripcion, "revisada_por": c.revisada_por, "primero": c.primer_reporte_at.isoformat(),
                    "ultimo": c.ultimo_reporte_at.isoformat(), "ejemplo": (example or "")[:280]})
    return out


async def review_campaign(session: AsyncSession, campana_id: UUID, *, por: str, regla: bool, descripcion: str | None = None,
                          nombre: str | None = None, estado: str | None = None) -> Campana | None:
    campana = await session.get(Campana, campana_id)
    if campana is None:
        return None
    campana.regla = regla
    campana.descripcion = (descripcion or "").strip()[:400] or None
    if nombre and nombre.strip():
        campana.nombre = nombre.strip()[:120]
    if estado in ("activa", "descartada"):
        campana.estado = estado
    campana.revisada_por, campana.revisada_at = por.strip()[:60] or "equipo", utcnow()
    return campana


async def create_campaign(session: AsyncSession, *, nombre: str, modalidad: str | None, descripcion: str, ejemplo: str,
                          por: str) -> Campana | None:
    """A campaign the team saw first (news, an entity's warning): from an example message. None if it is too short."""
    huella = archivista.fingerprint(ejemplo)
    if huella is None:
        return None
    campana = Campana(nombre=nombre.strip()[:120], modalidad=modalidad, centroide=huella, total_reportes=0, regla=True,
                      descripcion=descripcion.strip()[:400], revisada_por=por.strip()[:60] or "equipo", revisada_at=utcnow())
    session.add(campana)
    await session.flush()
    return campana


async def count_today(session: AsyncSession) -> int:
    return (await session.scalar(select(func.count()).select_from(Verificacion).where(Verificacion.creado_at >= utcnow() - timedelta(hours=24)))) or 0
