import logging

from fastapi import APIRouter, BackgroundTasks

from app.db import repository
from app.db.database import SessionLocal
from app.engine.analyzer import analyze_with_ollama
from app.schemas.contract import AnalysisInput, AnalysisResult

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(payload: AnalysisInput, background_tasks: BackgroundTasks) -> AnalysisResult:
    try:
        result = await analyze_with_ollama(payload)
    except Exception:
        logger.exception("Analysis engine failed")
        result = AnalysisResult(
            risk_level="inconclusive",
            risk_score=0,
            summary="No fue posible completar el análisis en este momento.",
            limitations=["El motor de análisis no está disponible temporalmente."],
        )

    if SessionLocal is not None:
        # Save after the response is sent, so a slow database never delays the bot.
        background_tasks.add_task(_save_analysis, payload, result)
    return result


async def _save_analysis(payload: AnalysisInput, result: AnalysisResult) -> None:
    try:
        await repository.save_analysis(payload, result)
    except Exception:
        # Persistence is best-effort; do not expose database errors or affect analysis.
        logger.warning("Analysis persistence unavailable")
