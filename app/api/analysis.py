"""Public analysis: the Dashboard's 'Verificar un mensaje' box and any API client. Rate limited by IP."""

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import session
from app.core.ratelimit import limit_by_ip
from app.core.security import normalize_phone
from app.engine import cerebro, traductor
from app.engine.juez import MODALIDADES, risk_level
from app.schemas.contract import AnalysisInput, AnalysisResult, RiskLevel
from app.services import banco, verificaciones

logger = logging.getLogger(__name__)
router = APIRouter()

CANALES = {"telegram", "dashboard", "api"}
FALLBACK = AnalysisResult(
    risk_level=RiskLevel.INCONCLUSIVE,
    risk_score=0,
    summary="No fue posible completar el análisis en este momento.",
    limitations=["El motor de análisis no está disponible temporalmente."],
)


async def run_analysis(db: AsyncSession, payload: AnalysisInput, background: BackgroundTasks, *, tipo_registro: str,
                       usuario_id: UUID | None = None, extracted: str | None = None) -> AnalysisResult:
    """Analyze, answer at once and save afterwards, so a slow database never delays the person."""
    try:
        result, huella, found = await cerebro.analyze(db, payload)
    except Exception:
        logger.exception("Analysis engine failed")
        return FALLBACK.model_copy(deep=True)
    result.verification_id = str(uuid4())
    result.extracted_text = extracted
    canal = payload.source if payload.source in CANALES else "api"
    background.add_task(verificaciones.save, UUID(result.verification_id), usuario_id=usuario_id, canal=canal,
                        tipo=tipo_registro, text=payload.text, result=result, huella=huella, pistas=found)
    return result


@router.post("/analyze", response_model=AnalysisResult, dependencies=[Depends(limit_by_ip)])
async def analyze(payload: AnalysisInput, background_tasks: BackgroundTasks, db: AsyncSession = Depends(session)) -> AnalysisResult:
    tipo = {"compra": "compra", "llamada": "voz"}.get(payload.tipo, "mensaje")
    return await run_analysis(db, payload, background_tasks, tipo_registro=tipo)


async def read_upload(file: UploadFile, limit: int) -> bytes:
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail="El archivo es demasiado grande.")
    return data


async def text_from_image(file: UploadFile) -> str:
    try:
        text = await traductor.read_image(await read_upload(file, traductor.MAX_IMAGE_BYTES))
    except traductor.ArchivoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if len(text.strip()) < 4:
        raise HTTPException(status_code=422, detail="No encontré texto en la imagen. Envía una captura donde se lea el mensaje.")
    return text[:4000]


async def text_from_audio(file: UploadFile) -> str:
    try:
        text = await traductor.transcribe(await read_upload(file, traductor.MAX_AUDIO_BYTES))
    except traductor.ArchivoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if len(text.strip()) < 4:
        raise HTTPException(status_code=422, detail="No entendí la nota de voz. Intenta grabarla de nuevo, más cerca del micrófono.")
    return text[:4000]


@router.post("/analyze/imagen", response_model=AnalysisResult, dependencies=[Depends(limit_by_ip)])
async def analyze_image(background_tasks: BackgroundTasks, file: UploadFile = File(...), tipo: str = Form("mensaje"),
                        source: str = Form("dashboard"), db: AsyncSession = Depends(session)) -> AnalysisResult:
    text = await text_from_image(file)
    payload = AnalysisInput(text=text, source=source, tipo="compra" if tipo == "compra" else "mensaje")
    return await run_analysis(db, payload, background_tasks, tipo_registro="compra" if tipo == "compra" else "captura", extracted=text)


@router.post("/analyze/voz", response_model=AnalysisResult, dependencies=[Depends(limit_by_ip)])
async def analyze_voice(background_tasks: BackgroundTasks, file: UploadFile = File(...), source: str = Form("dashboard"),
                        db: AsyncSession = Depends(session)) -> AnalysisResult:
    text = await text_from_audio(file)
    payload = AnalysisInput(text=text, source=source, tipo="llamada")
    return await run_analysis(db, payload, background_tasks, tipo_registro="voz", extracted=text)


def normalize_value(tipo: str, valor: str) -> tuple[str, str]:
    """('llave_breb', '315 000 0000') -> ('llave', '3150000000'), as docs/01 names the types."""
    tipo = {"llave_breb": "llave", "numero": "telefono"}.get(tipo, tipo)
    if tipo not in ("telefono", "llave", "cuenta", "enlace"):
        raise HTTPException(status_code=422, detail="Tipo no válido: usa telefono, llave, cuenta o enlace.")
    if tipo == "telefono":
        phone = normalize_phone(valor)
        if phone is None:
            raise HTTPException(status_code=422, detail="El número no es válido.")
        return tipo, phone
    valor = valor.strip()
    return tipo, ("".join(valor.split()) if valor[:1].isdigit() else valor.lower())


def describe_hit(hit) -> dict:
    if hit is None:
        return {"encontrado": False, "nivel": 0, "palabra": "Sin reportes", "personas": 0, "reportes": 0}
    word = "Oficial" if hit.oficial_de else ("En revisión" if hit.estado == "en_revision" else
                                              {"high": "Alto riesgo", "medium": "Sospechoso", "low": "Bajo riesgo"}[risk_level(hit.nivel).value])
    return {"encontrado": True, "valor": hit.visible, "nivel": hit.nivel, "palabra": word, "personas": hit.personas,
            "reportes": hit.reportes, "modalidad": MODALIDADES.get(hit.modalidad or "", (None,))[0], "estado": hit.estado,
            "oficial_de": hit.oficial_de, "sitio": hit.sitio}


@router.get("/banco/consultar", dependencies=[Depends(limit_by_ip)])
async def lookup_value(tipo: str, valor: str, db: AsyncSession = Depends(session)) -> dict:
    tipo, valor = normalize_value(tipo, valor)
    return describe_hit(await banco.lookup(db, tipo, valor))
