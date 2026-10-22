"""Team-only actions (ADMIN_API_KEY): entities, the official-number list and review requests."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import normalize_value
from app.api.deps import session
from app.core.security import require_admin
from app.services import banco, entidades

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/equipo/yo")
async def whoami() -> dict:
    """Lets the Dashboard check the team key before it shows the moderation tools."""
    return {"equipo": True}


class EntidadIn(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=80)
    tipo: str = Field("banco", pattern=r"^(banco|tienda|operador|publica)$")
    dominio_oficial: str | None = None
    lineas_oficiales: list[str] = Field(default_factory=list)
    correo: str | None = Field(None, min_length=5, max_length=120, description="Para entrar al Panel con correo y contraseña")


@router.post("/entidades")
async def create_entity(body: EntidadIn, db: AsyncSession = Depends(session)) -> dict:
    if await entidades.by_name(db, body.nombre):
        raise HTTPException(status_code=409, detail="Esa entidad ya existe.")
    entidad, key = await entidades.create(db, body.nombre, body.tipo, body.dominio_oficial, body.lineas_oficiales)
    answer = {"nombre": entidad.nombre, "api_key": key, "aviso": "Guarda la llave y la contraseña: no se vuelven a mostrar."}
    if body.correo:
        answer |= {"correo": body.correo.strip().lower(), "clave": await entidades.add_access(db, entidad, body.correo)}
    return answer


class ListaBlancaIn(BaseModel):
    entidad: str
    valor: str
    canal: str = Field("telegram", pattern=r"^(telegram|whatsapp|llamada|sms)$")
    verificado_por: str = Field("equipo", max_length=60)


@router.post("/banco/lista-blanca")
async def add_official(body: ListaBlancaIn, db: AsyncSession = Depends(session)) -> dict:
    entidad = await entidades.by_name(db, body.entidad)
    if entidad is None:
        raise HTTPException(status_code=404, detail="No existe esa entidad.")
    tipo, valor = normalize_value("telefono", body.valor)
    numero = await banco.add_official(db, entidad, tipo, valor, body.canal, "pagina_oficial", body.verificado_por)
    return {"valor": numero.valor_visible, "entidad": entidad.nombre}


class ResolverIn(BaseModel):
    aceptar: bool


@router.post("/banco/revisiones/{solicitud_id}")
async def resolve_review(solicitud_id: UUID, body: ResolverIn, db: AsyncSession = Depends(session)) -> dict:
    solicitud = await banco.resolve_review(db, solicitud_id, body.aceptar)
    if solicitud is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe o ya se resolvió.")
    return {"estado": solicitud.estado}
