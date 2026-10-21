import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from app.core.config import settings
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router
from app.engine.analyzer import warm_up


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model before serving, so "Application startup complete" means the first analysis is fast.
    await warm_up()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["Analysis"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled server error")
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
