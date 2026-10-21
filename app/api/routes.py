import logging

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.db import repository
from app.db.database import SessionLocal
from app.engine.analyzer import analyze_with_ollama
from app.schemas.contract import AnalysisInput, AnalysisResult, FeedbackInput, FeedbackResult, HistoryItem

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(payload: AnalysisInput) -> AnalysisResult:
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
        try:
            await repository.save_analysis(payload, result)
        except Exception:
            logger.warning("Analysis persistence unavailable")
    return result


@router.post("/feedback", response_model=FeedbackResult)
async def submit_feedback(payload: FeedbackInput) -> FeedbackResult:
    try:
        record = await repository.save_feedback(payload.analysis_id, payload.feedback_type, payload.comment)
        return FeedbackResult(id=record.id, analysis_id=record.analysis_id,
                              feedback_type=record.feedback_type, comment=record.comment)
    except Exception:
        logger.warning("Feedback persistence unavailable")
        raise HTTPException(status_code=503, detail="No fue posible guardar el comentario temporalmente.")


@router.get("/history", response_model=list[HistoryItem])
async def get_history(user_ref: str | None = None, limit: int = Query(default=50, ge=1, le=100),
                      before: datetime | None = None) -> list[HistoryItem]:
    try:
        rows = await repository.list_analyses(limit=limit, user_ref=user_ref, before=before)
        return [HistoryItem(id=row.id, created_at=row.created_at, source=row.source,
                            user_ref=row.user_ref, risk_level=row.risk_level, risk_score=row.risk_score,
                            summary=row.summary, analysis_version=row.analysis_version) for row in rows]
    except Exception:
        logger.warning("History unavailable")
        return []
