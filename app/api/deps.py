from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import session_entity_id
from app.db.database import SessionLocal
from app.db.models import Entidad
from app.services import entidades


async def session() -> AsyncGenerator[AsyncSession, None]:
    """One transaction per request: committed if the endpoint returns, rolled back if it fails.

    Use it as Depends(session, scope="function"): the commit then happens as soon as the endpoint returns, before
    the background tasks (saving an analysis) run. With the default scope, FastAPI closes it after the response,
    and a background save would wait for the request's own uncommitted transaction.
    """
    async with SessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def require_entity(x_entity_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None),
                         db: AsyncSession = Depends(session, scope="function")) -> Entidad:
    """The panel signs in with e-mail and password and sends a session; integrations send the API key."""
    entidad = None
    if authorization and authorization.startswith("Bearer "):
        entity_id = session_entity_id(authorization.removeprefix("Bearer ").strip())
        entidad = await entidades.by_id(db, entity_id) if entity_id else None
    elif x_entity_api_key:
        entidad = await entidades.by_api_key(db, x_entity_api_key)
    if entidad is None:
        raise HTTPException(status_code=401, detail="Tu sesión terminó o el acceso no es válido.")
    return entidad
