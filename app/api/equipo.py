"""Team-only actions (ADMIN_API_KEY): entities, the official-number list, review requests, campaigns and case traces."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import normalize_value
from app.api.deps import session
from app.core.security import require_admin
from app.engine.juez import MODALIDADES
from app.services import banco, casos, entidades, verificaciones

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
async def create_entity(body: EntidadIn, db: AsyncSession = Depends(session, scope="function")) -> dict:
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
async def add_official(body: ListaBlancaIn, db: AsyncSession = Depends(session, scope="function")) -> dict:
    entidad = await entidades.by_name(db, body.entidad)
    if entidad is None:
        raise HTTPException(status_code=404, detail="No existe esa entidad.")
    tipo, valor = normalize_value("telefono", body.valor)
    numero = await banco.add_official(db, entidad, tipo, valor, body.canal, "pagina_oficial", body.verificado_por)
    return {"valor": numero.valor_visible, "entidad": entidad.nombre}


class ResolverIn(BaseModel):
    aceptar: bool


@router.post("/banco/revisiones/{solicitud_id}")
async def resolve_review(solicitud_id: UUID, body: ResolverIn, db: AsyncSession = Depends(session, scope="function")) -> dict:
    solicitud = await banco.resolve_review(db, solicitud_id, body.aceptar)
    if solicitud is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe o ya se resolvió.")
    return {"estado": solicitud.estado}


@router.get("/equipo/campanas")
async def campaigns(db: AsyncSession = Depends(session, scope="function")) -> dict:
    """Detected and identified campaigns, with an anonymized example of each, for the team to review."""
    return {"campanas": await verificaciones.campaigns_for_review(db), "regla_automatica": verificaciones.REGLA_AUTOMATICA,
            "modalidades": {k: v[0] for k, v in MODALIDADES.items()}}


class CampanaIn(BaseModel):
    regla: bool = Field(True, description="Identificada por el equipo: el bot la reconoce sin límite de días")
    descripcion: str | None = Field(None, max_length=400, description="Cómo funciona, en palabras simples: el bot la cita")
    nombre: str | None = Field(None, max_length=120)
    estado: str | None = Field(None, pattern=r"^(activa|descartada)$")
    revisada_por: str = Field("equipo", max_length=60)


@router.post("/equipo/campanas/{campana_id}")
async def review_campaign(campana_id: UUID, body: CampanaIn, db: AsyncSession = Depends(session, scope="function")) -> dict:
    campana = await verificaciones.review_campaign(db, campana_id, por=body.revisada_por, regla=body.regla,
                                                   descripcion=body.descripcion, nombre=body.nombre, estado=body.estado)
    if campana is None:
        raise HTTPException(status_code=404, detail="Esa campaña no existe.")
    return {"id": str(campana.id), "nombre": campana.nombre, "regla": bool(campana.regla), "estado": campana.estado}


class NuevaCampanaIn(BaseModel):
    nombre: str = Field(..., min_length=4, max_length=120)
    modalidad: str | None = None
    descripcion: str = Field(..., min_length=10, max_length=400)
    ejemplo: str = Field(..., min_length=20, max_length=4000, description="Un mensaje real de la campaña, sin datos personales")
    revisada_por: str = Field("equipo", max_length=60)


@router.post("/equipo/campanas")
async def new_campaign(body: NuevaCampanaIn, db: AsyncSession = Depends(session, scope="function")) -> dict:
    """A campaign the team saw before the bot did (news, an entity's warning), as a rule from an example message."""
    modalidad = body.modalidad if body.modalidad in MODALIDADES else None
    campana = await verificaciones.create_campaign(db, nombre=body.nombre, modalidad=modalidad, descripcion=body.descripcion,
                                                   ejemplo=body.ejemplo, por=body.revisada_por)
    if campana is None:
        raise HTTPException(status_code=422, detail="El ejemplo es muy corto para reconocer la campaña: pega el mensaje completo.")
    return {"id": str(campana.id), "nombre": campana.nombre, "regla": True}


@router.get("/equipo/casos/{referencia}")
async def case_trace(referencia: str, db: AsyncSession = Depends(session, scope="function")) -> dict:
    """Registro trazable for the team: any case by its reference, with the anonymized text and no relatives' names."""
    ref = casos.parse(referencia)
    found = await casos.find(db, ref) if ref else None
    if found is None:
        raise HTTPException(status_code=404, detail="No encontré ese caso.")
    return await casos.trace(db, found, names=False) | {"texto": found.texto_anonimizado}
