import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import text

from app.api.routes import router as api_router
from app.bot import webhook as telegram_webhook
from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.engine.analyzer import warm_up
from app.engine.traductor import warm_up_models
from app.services import demo, llamadas

logger = logging.getLogger(__name__)


async def _expire_calls_forever() -> None:
    # pg_cron in the guide; here a loop: registered calls are wiped 15 minutes after they are created.
    while True:
        try:
            async with SessionLocal() as db:
                await llamadas.expire(db)
                await db.commit()
        except Exception:
            logger.warning("Could not expire registered calls", exc_info=True)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Load every model before serving: "Application startup complete" means the first analysis is fast,
    # and OCR/Whisper loading does not compete for the CPU with the first requests.
    if settings.IA_LOCAL:
        await warm_up()
    if settings.PRECARGAR_MODELOS:
        await warm_up_models()
    background = [asyncio.create_task(_expire_calls_forever())]
    app.state.telegram = await telegram_webhook.start()  # None on your computer: there the bot runs by polling
    yield
    if app.state.telegram is not None:
        await telegram_webhook.stop(app.state.telegram)
    for task in background:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.DASHBOARD_ORIGINS.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Entity-API-Key", "X-Admin-Key"],  # Authorization: the panel session
)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(telegram_webhook.router)
app.state.telegram = None


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled server error")
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})


@app.get("/health", tags=["Health"])
async def health_check():
    database = ai = "ok"
    with_demo = False
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            with_demo = await demo.present(db)
    except Exception:
        database = "no disponible"
    if not settings.IA_LOCAL:
        ai = "apagada"  # the rules answer alone
    else:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                (await client.get(f"{settings.OLLAMA_HOST}/api/version")).raise_for_status()
        except httpx.HTTPError:
            ai = "no disponible"
    return {
        "status": "ok" if database == "ok" else "degradado",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "base_de_datos": database,
        "ia": ai,
        "demo": with_demo,  # the Dashboard says "Datos de demostración" only while seed_demo.py's data is loaded
    }

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
