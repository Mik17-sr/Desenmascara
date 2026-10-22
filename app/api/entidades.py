"""Panel de la entidad: banks and stores sign in with e-mail and password to register their calls and
official numbers. Integrations send their API key instead."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import normalize_value
from app.api.deps import require_entity, session
from app.core.ratelimit import limit_by_ip
from app.core.security import new_session
from app.db.models import Entidad
from app.services import banco, dashboard, entidades, llamadas

router = APIRouter()


class RegistrarIn(BaseModel):
    telefono_cliente: str = Field(..., min_length=7, max_length=20)
    motivo: str = Field(..., min_length=3, max_length=120)
    asesor: str = Field(..., min_length=2, max_length=60)


SESSION_HOURS = 12
REMEMBERED_HOURS = 30 * 24  # "Recordar en este equipo"


class IngresarIn(BaseModel):
    correo: str = Field(..., min_length=5, max_length=120)
    clave: str = Field(..., min_length=1, max_length=200)
    recordar: bool = False


class SesionIn(BaseModel):
    recordar: bool = True


def _session(entidad: Entidad, remember: bool) -> dict:
    hours = REMEMBERED_HOURS if remember else SESSION_HOURS
    return {"token": new_session(str(entidad.id), hours), "nombre": entidad.nombre, "vence_en_horas": hours}


@router.post("/entidad/ingresar", dependencies=[Depends(limit_by_ip)])
async def sign_in(body: IngresarIn, db: AsyncSession = Depends(session, scope="function")) -> dict:
    """The panel's sign-in. Same answer for an unknown e-mail and a wrong password; tries are limited per IP."""
    entidad = await entidades.by_login(db, body.correo, body.clave)
    if entidad is None:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    return _session(entidad, body.recordar)


@router.post("/entidad/sesion")
async def session_from_key(body: SesionIn, entidad: Entidad = Depends(require_entity)) -> dict:
    """Swaps the API key (sign-in links, integrations) for a panel session, so the panel never keeps the key."""
    return _session(entidad, body.recordar)


@router.get("/entidad/alertas")
async def brand_alerts(entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session, scope="function")) -> dict:
    """Early warning: the scams that used this entity's name in the last 30 days, as the community reported them."""
    found = (await dashboard.brands(db, only=entidad.nombre) or [None])[0]
    empty = {"mensajes": 0, "hoy": 0, "ultimo": None, "modalidades": [], "dominios": [], "ejemplo": None}
    return {"marca": entidad.nombre, "dias": 30} | ({k: found[k] for k in empty} if found else empty)


@router.get("/entidad/yo")
async def whoami(entidad: Entidad = Depends(require_entity)) -> dict:
    return {"nombre": entidad.nombre, "tipo": entidad.tipo, "dominio_oficial": entidad.dominio_oficial}


@router.post("/llamadas/registrar")
async def register_call(body: RegistrarIn, entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session, scope="function")) -> dict:
    """Contract of docs/01 section 5A."""
    try:
        llamada, code = await llamadas.register(db, entidad, body.telefono_cliente, body.motivo, body.asesor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"success": True, "codigo_verificacion": code, "expires_in_seconds": int(llamadas.CODE_TTL.total_seconds()),
            "registro_id": str(llamada.id), "vence_at": llamada.vence_at.isoformat() + "Z"}


@router.get("/llamadas/hoy")
async def calls_today(entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session, scope="function")) -> list[dict]:
    return [
        {"id": str(c.id), "cliente": c.telefono_visible, "motivo": c.motivo, "asesor": c.asesor, "estado": c.estado,
         "creado": c.creado_at.isoformat() + "Z", "vence": c.vence_at.isoformat() + "Z"}
        for c in await llamadas.today(db, entidad)
    ]


class OficialIn(BaseModel):
    valor: str = Field(..., min_length=7, max_length=20)
    canal: str = Field("telegram", pattern=r"^(telegram|whatsapp|llamada|sms)$")


@router.post("/entidad/numeros-oficiales")
async def register_official(body: OficialIn, entidad: Entidad = Depends(require_entity), db: AsyncSession = Depends(session, scope="function")) -> dict:
    tipo, valor = normalize_value("telefono", body.valor)
    numero = await banco.add_official(db, entidad, tipo, valor, body.canal, "registro", entidad.nombre)
    return {"valor": numero.valor_visible, "canal": numero.canal}
