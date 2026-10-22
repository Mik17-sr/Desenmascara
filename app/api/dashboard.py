"""Read-only, aggregated and anonymous: what the public Dashboard views can see."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import session
from app.services import dashboard

router = APIRouter(prefix="/dashboard")


@router.get("/radar")
async def radar(db: AsyncSession = Depends(session, scope="function")) -> dict:
    return await dashboard.radar(db)


@router.get("/impacto")
async def impact(db: AsyncSession = Depends(session, scope="function")) -> dict:
    return await dashboard.impact(db)


@router.get("/marcas")
async def brands(db: AsyncSession = Depends(session, scope="function")) -> list[dict]:
    """The entities scams impersonate (30 days): name, how many messages and the usual modality, never a text."""
    return [{k: b[k] for k in ("marca", "mensajes", "hoy", "ultimo", "modalidad")} for b in await dashboard.brands(db)]


@router.get("/banco")
async def banco(db: AsyncSession = Depends(session, scope="function")) -> dict:
    return await dashboard.banco_view(db)
