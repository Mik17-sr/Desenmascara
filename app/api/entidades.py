"""Panel de la entidad: banks and stores register their calls and official numbers with their API key."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import normalize_value
from app.api.deps import require_entity, session
from app.db.models import Entidad
from app.services import banco, llamadas

router = APIRouter()


class RegistrarIn(BaseModel):
    telefono_cliente: str = Field(..., min_length=7, max_length=20)
    motivo: str = Field(..., min_length=3, max_length=120)
    asesor: str = Field(..., min_length=2, max_length=60)


@router.get("/entidad/yo")
async def whoami(entidad: Entidad = Depends(require_entity)) -> dict:
    return {"nombre": entidad.nombre, "tipo": entidad.tipo, "dominio_oficial": entidad.dominio_oficial}


@router.post("/llamadas/registrar")
async def register_call(body: RegistrarIn, entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session)) -> dict:
    """Contract of docs/01 section 5A."""
    try:
        llamada, code = await llamadas.register(db, entidad, body.telefono_cliente, body.motivo, body.asesor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"success": True, "codigo_verificacion": code, "expires_in_seconds": int(llamadas.CODE_TTL.total_seconds()),
            "registro_id": str(llamada.id), "vence_at": llamada.vence_at.isoformat() + "Z"}


@router.get("/llamadas/hoy")
async def calls_today(entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session)) -> list[dict]:
    return [
        {"id": str(c.id), "cliente": c.telefono_visible, "motivo": c.motivo, "asesor": c.asesor, "estado": c.estado,
         "creado": c.creado_at.isoformat() + "Z", "vence": c.vence_at.isoformat() + "Z"}
        for c in await llamadas.today(db, entidad)
    ]


class OficialIn(BaseModel):
    valor: str = Field(..., min_length=7, max_length=20)
    canal: str = Field("telegram", pattern=r"^(telegram|whatsapp|llamada|sms)$")


@router.post("/entidad/numeros-oficiales")
async def register_official(body: OficialIn, entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session)) -> dict:
    tipo, valor = normalize_value("telefono", body.valor)
    numero = await banco.add_official(db, entidad, tipo, valor, body.canal, "registro", entidad.nombre)
    return {"valor": numero.valor_visible, "canal": numero.canal}
