from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import SessionLocal
from app.db.models import AnalysisModel, FeedbackModel
from app.schemas.contract import AnalysisInput, AnalysisResult


async def save_analysis(
    payload: AnalysisInput, result: AnalysisResult, session: AsyncSession | None = None
) -> AnalysisModel:
    """Persist summary metadata only; the original message is never stored."""
    if session is not None:
        record = AnalysisModel(
            source=payload.source,
            user_ref=payload.user_ref,
            risk_level=result.risk_level.value,
            risk_score=result.risk_score,
            summary=result.summary,
            analysis_version=result.analysis_version,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    if SessionLocal is None:
        raise RuntimeError("Database is not configured")
    async with SessionLocal() as db_session:
        return await save_analysis(payload, result, db_session)


async def get_analysis(analysis_id: UUID, session: AsyncSession | None = None) -> AnalysisModel | None:
    if session is not None:
        return await session.get(AnalysisModel, analysis_id)
    if SessionLocal is None:
        raise RuntimeError("Database is not configured")
    async with SessionLocal() as db_session:
        return await get_analysis(analysis_id, db_session)


async def save_feedback(analysis_id: UUID, feedback_type: str, comment: str | None = None,
                        session: AsyncSession | None = None) -> FeedbackModel:
    if session is not None:
        record = FeedbackModel(analysis_id=analysis_id, feedback_type=feedback_type, comment=comment)
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record
    if SessionLocal is None:
        raise RuntimeError("Database is not configured")
    async with SessionLocal() as db_session:
        return await save_feedback(analysis_id, feedback_type, comment, db_session)


async def list_analyses(limit: int = 50, user_ref: str | None = None,
                        before: object | None = None, session: AsyncSession | None = None) -> list[AnalysisModel]:
    limit = max(1, min(limit, 100))
    if session is not None:
        query = select(AnalysisModel)
        if user_ref is not None:
            query = query.where(AnalysisModel.user_ref == user_ref)
        if before is not None:
            query = query.where(AnalysisModel.created_at < before)
        rows = await session.scalars(query.order_by(AnalysisModel.created_at.desc()).limit(limit))
        return list(rows)
    if SessionLocal is None:
        raise RuntimeError("Database is not configured")
    async with SessionLocal() as db_session:
        return await list_analyses(limit, user_ref, before, db_session)
