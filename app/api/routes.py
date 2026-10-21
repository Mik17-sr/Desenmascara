from fastapi import APIRouter

from app.api import analysis, bot, dashboard, entidades, equipo

router = APIRouter()
router.include_router(analysis.router, tags=["Analysis"])
router.include_router(bot.router, tags=["Bot"])
router.include_router(entidades.router, tags=["Entidades"])
router.include_router(equipo.router, tags=["Equipo"])
router.include_router(dashboard.router, tags=["Dashboard"])
