"""Read-only, aggregated and anonymous: what the public Dashboard views can see."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import session
from app.services import dashboard

router = APIRouter(prefix="/dashboard")


@router.get("/radar")
async def radar(db: AsyncSession = Depends(session)) -> dict:
    return await dashboard.radar(db)


@router.get("/banco")
async def banco(db: AsyncSession = Depends(session)) -> dict:
    return await dashboard.banco_view(db)
