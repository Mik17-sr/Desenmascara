from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import SessionLocal
from app.db.models import Entidad
from app.services import entidades


async def session() -> AsyncGenerator[AsyncSession, None]:
    """One transaction per request: committed if the endpoint returns, rolled back if it fails."""
    async with SessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def require_entity(x_entity_api_key: str | None = Header(default=None), db: AsyncSession = Depends(session)) -> Entidad:
    entidad = await entidades.by_api_key(db, x_entity_api_key) if x_entity_api_key else None
    if entidad is None:
        raise HTTPException(status_code=401, detail="Llave de acceso no válida.")
    return entidad
