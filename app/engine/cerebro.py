"""The brain: runs the six reviews and hands the evidence to the judge (guide section 11).

The AI call, the domain registry and the reputation list run at the same time; everything
else is local and takes milliseconds, so the AI sets the total time.
"""

import asyncio
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine import archivista, enlaces, pistas as pistas_mod
from app.engine.analyzer import INJECTION_PATTERN, MAX_MODEL_CHARS, classify
from app.engine.juez import Evidencia, judge
from app.schemas.contract import AnalysisInput, AnalysisResult
from app.services import banco, entidades, verificaciones


async def _no_ai():
    return None


async def analyze(session: AsyncSession, payload: AnalysisInput) -> tuple[AnalysisResult, list[int] | None, pistas_mod.Pistas]:
    started = time.perf_counter()
    official = await entidades.official_domains(session)
    known = [e.nombre for e in await entidades.active(session)]
    found = pistas_mod.extract(payload.text, known)
    urls = list(dict.fromkeys(found.urls + pistas_mod.extract_urls(" ".join(payload.links))))[:5]
    found.urls = urls
    checks = [enlaces.check_link(u, official, found.entidades) for u in urls]
    unofficial = list(dict.fromkeys(c.dominio for c in checks if not c.oficial_de))

    injection = bool(INJECTION_PATTERN.search(payload.text))
    psicologia, ages, flagged = await asyncio.gather(
        _no_ai() if injection else classify(payload.text),
        enlaces.domain_ages(unofficial),
        enlaces.reputation(urls),
    )

    hits = []
    for tipo, values in (("telefono", found.telefonos), ("llave", found.llaves), ("cuenta", found.cuentas), ("enlace", unofficial)):
        for value in values[:3]:
            hit = await banco.lookup(session, tipo, value)
            if hit:
                hits.append(hit)

    huella = archivista.fingerprint(payload.text)
    evidencia = Evidencia(
        tipo=payload.tipo, pistas=found, links=checks, ages=ages, flagged_urls=flagged, psicologia=psicologia,
        ia_consultada=not injection, inyeccion=injection, campana=await verificaciones.best_campaign(session, huella), banco=hits,
    )
    result = judge(evidencia)
    if len(payload.text) > MAX_MODEL_CHARS and not injection:
        result.limitations.append("El mensaje es largo: la IA leyó solo el inicio y el final.")
    result.processing_ms = round((time.perf_counter() - started) * 1000)
    return result, huella, found
