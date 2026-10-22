"""Endpoints the Telegram bot calls on behalf of a person. Protected by BOT_API_SECRET.

The API never stores Telegram ids or phones in clear: only their HMAC, plus the encrypted
chat id it needs to write to Círculo members.
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import describe_hit, normalize_value, run_analysis, text_from_audio, text_from_image
from app.api.deps import session
from app.core.ratelimit import RateLimiter, bot_user_limiter, report_limiter
from app.core.security import require_bot
from app.db.models import Usuario
from app.engine.juez import MODALIDADES, risk_level
from app.engine.oficiales import line_to_call, official_websites
from app.engine.pistas import Pistas, extract
from app.schemas.contract import AnalysisInput, AnalysisResult, RiskLevel, SignalItem, SignalSource
from app.services import banco, circulo, entidades, llamadas, usuarios, verificaciones

router = APIRouter(prefix="/bot", dependencies=[Depends(require_bot)])


class Persona(BaseModel):
    telegram_id: int
    chat_id: int
    nombre: str | None = None


class AnalizarIn(Persona):
    texto: str = Field(..., min_length=1, max_length=4000)
    tipo: str = "mensaje"
    enlaces: list[str] = Field(default_factory=list)
    reenviado_de: int | None = Field(default=None, description="Telegram id del autor original, si es un reenvío")


class Pregunta(BaseModel):
    aviso_id: str
    chat_id: int
    nombre: str


class AnalizarOut(BaseModel):
    resultado: AnalysisResult
    preguntas_circulo: list[Pregunta] = Field(default_factory=list)
    avisar_familiares: list[int] = Field(default_factory=list)


async def _user(db: AsyncSession, persona: Persona) -> Usuario:
    return await usuarios.get_or_create(db, persona.telegram_id, persona.chat_id, persona.nombre)


async def _consented(db: AsyncSession, persona: Persona, limiter: RateLimiter = bot_user_limiter) -> Usuario:
    user = await _user(db, persona)
    if user.consentimiento_at is None:
        raise HTTPException(status_code=403, detail="Falta el consentimiento para tratar los datos.")
    limiter.check(user.telegram_hash)
    return user


@router.post("/inicio")
async def start(persona: Persona, db: AsyncSession = Depends(session)) -> dict:
    user = await _user(db, persona)
    return {"consentimiento": user.consentimiento_at is not None, "telefono_verificado": bool(user.telefono_hash),
            "tiene_circulo": bool(await circulo.members(db, user))}


@router.post("/consentimiento")
async def consent(persona: Persona, db: AsyncSession = Depends(session)) -> dict:
    usuarios.set_consent(await _user(db, persona))
    return {"ok": True}


class TelefonoIn(Persona):
    telefono: str


@router.post("/telefono")
async def share_phone(body: TelefonoIn, db: AsyncSession = Depends(session)) -> dict:
    try:
        await usuarios.set_phone(db, await _user(db, body), body.telefono)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="No pude leer ese número.") from exc
    return {"ok": True}


async def _circle_actions(db: AsyncSession, user: Usuario, result: AnalysisResult, text: str,
                          reenviado_de: int | None) -> tuple[list[Pregunta], list[int]]:
    """Falso familiar -> ask the real relative. Any other high risk -> let the Círculo know in time."""
    if not await circulo.members(db, user):
        return [], []
    if result.modalidad == "falso_familiar":
        sender = await usuarios.by_telegram(db, reenviado_de) if reenviado_de else None
        avisos = await circulo.ask(db, user, text, None, sender=sender)
        return [Pregunta(aviso_id=str(a.id), chat_id=usuarios.chat_id_of(u), nombre=m.nombre) for a, m, u in avisos], []
    if result.risk_level == RiskLevel.HIGH:
        return [], [usuarios.chat_id_of(u) for u in await circulo.alert_all(db, user)]
    return [], []


async def _analyze_for(db: AsyncSession, user: Usuario, body: AnalizarIn, background: BackgroundTasks, tipo_registro: str,
                       extracted: str | None = None) -> AnalizarOut:
    tipo = body.tipo if body.tipo in ("mensaje", "compra", "llamada") else "mensaje"
    payload = AnalysisInput(text=body.texto, source="telegram", tipo=tipo, links=body.enlaces)
    result = await run_analysis(db, payload, background, tipo_registro=tipo_registro, usuario_id=user.id, extracted=extracted)
    preguntas, avisar = await _circle_actions(db, user, result, body.texto, body.reenviado_de)
    return AnalizarOut(resultado=result, preguntas_circulo=preguntas, avisar_familiares=avisar)


@router.post("/analizar", response_model=AnalizarOut)
async def analyze(body: AnalizarIn, background_tasks: BackgroundTasks, db: AsyncSession = Depends(session)) -> AnalizarOut:
    user = await _consented(db, body)
    tipo_registro = {"compra": "compra", "llamada": "voz"}.get(body.tipo, "mensaje")
    return await _analyze_for(db, user, body, background_tasks, tipo_registro)


@router.post("/analizar-imagen", response_model=AnalizarOut)
async def analyze_image(background_tasks: BackgroundTasks, telegram_id: int = Form(...), chat_id: int = Form(...),
                        tipo: str = Form("mensaje"), file: UploadFile = File(...), db: AsyncSession = Depends(session)) -> AnalizarOut:
    persona = Persona(telegram_id=telegram_id, chat_id=chat_id)
    user = await _consented(db, persona)
    text = await text_from_image(file)
    body = AnalizarIn(telegram_id=telegram_id, chat_id=chat_id, texto=text, tipo=tipo)
    return await _analyze_for(db, user, body, background_tasks, "compra" if tipo == "compra" else "captura", extracted=text)


@router.post("/analizar-voz", response_model=AnalizarOut)
async def analyze_voice(background_tasks: BackgroundTasks, telegram_id: int = Form(...), chat_id: int = Form(...),
                        file: UploadFile = File(...), db: AsyncSession = Depends(session)) -> AnalizarOut:
    user = await _consented(db, Persona(telegram_id=telegram_id, chat_id=chat_id))
    text = await text_from_audio(file)
    body = AnalizarIn(telegram_id=telegram_id, chat_id=chat_id, texto=text, tipo="llamada")
    return await _analyze_for(db, user, body, background_tasks, "voz", extracted=text)


class LlamadaIn(Persona):
    texto: str


def _call_result(entidad: str, real: bool) -> AnalysisResult:
    """Llamada Verificada is a certainty, not a probability: no call registered means high risk."""
    code = "LLAMADA_REGISTRADA" if real else "LLAMADA_NO_REGISTRADA"
    label = f"{entidad} registró una llamada a tu número." if real else f"{entidad} no tiene ninguna llamada registrada hacia tu número."
    return AnalysisResult(
        risk_level=RiskLevel.LOW if real else RiskLevel.HIGH, risk_score=5 if real else 95,
        summary="La entidad confirmó la llamada." if real else "No es tu entidad.", modalidad=None if real else "falso_asesor",
        signals=[SignalItem(code=code, label=label, evidence=entidad, source=SignalSource.JUEZ, points=0 if real else 95)],
    )


@router.post("/llamada")
async def verified_call(body: LlamadaIn, background_tasks: BackgroundTasks, db: AsyncSession = Depends(session)) -> dict:
    user = await _consented(db, body)
    entidad = await entidades.find_in_text(db, body.texto)
    if entidad is None:
        connected = [e.nombre for e in await entidades.active(db) if e.tipo != "tienda"]
        named = extract(body.texto).entidades
        if named:  # a real entity that has not joined: say so, never "no es tu banco"
            sites = official_websites().get(named[0], ())
            line = line_to_call(named[0])
            return {"estado": "no_conectada", "entidad": named[0], "sitio": sites[0] if sites else None,
                    "linea": line.linea if line else None, "entidades": connected}
        return {"estado": "entidad_desconocida", "entidades": connected}
    if not user.telefono_hash:
        return {"estado": "falta_telefono", "entidad": entidad.nombre}
    found = await llamadas.consult(db, user, entidad)
    result = _call_result(entidad.nombre, real=found is not None)
    background_tasks.add_task(verificaciones.save, uuid4(), usuario_id=user.id, canal="telegram", tipo="llamada",
                              text=f"Consulta de Llamada Verificada: {entidad.nombre}", result=result, huella=None,
                              pistas=Pistas(), llamada_id=found[0].id if found else None)
    if found:
        llamada, code = found
        return {"estado": "real", "entidad": entidad.nombre, "motivo": llamada.motivo, "codigo": code}
    return {"estado": "no_registrada", "entidad": entidad.nombre, "lineas_oficiales": entidad.lineas_oficiales}


class CodigoIn(Persona):
    codigo: str = Field(..., pattern=r"^\d{4}$")


@router.post("/llamada/confirmar")
async def confirm_code(body: CodigoIn, db: AsyncSession = Depends(session)) -> dict:
    user = await _consented(db, body)
    found = await llamadas.confirm(db, user, body.codigo)
    return {"estado": "correcto", "entidad": found[1].nombre} if found else {"estado": "incorrecto"}


class ValorIn(Persona):
    valor: str = Field(..., min_length=3, max_length=120)
    tipo: str = "telefono"


@router.post("/numero")
async def check_number(body: ValorIn, background_tasks: BackgroundTasks, db: AsyncSession = Depends(session)) -> dict:
    user = await _consented(db, body)
    tipo, valor = normalize_value(body.tipo, body.valor)
    hit = await banco.lookup(db, tipo, valor)
    info = describe_hit(hit)
    level = risk_level(hit.nivel) if hit and not hit.oficial_de and hit.estado != "en_revision" else RiskLevel.LOW
    result = AnalysisResult(risk_level=level, risk_score=hit.nivel if hit else 0, summary=info["palabra"],
                            modalidad=hit.modalidad if hit else None)
    background_tasks.add_task(verificaciones.save, uuid4(), usuario_id=user.id, canal="telegram", tipo="numero",
                              text=f"Consulta de {tipo}", result=result, huella=None, pistas=Pistas())
    return info | {"tipo": tipo}


class ReporteIn(ValorIn):
    modalidad: str | None = None
    verificacion_id: str | None = None


@router.post("/reportar")
async def report(body: ReporteIn, db: AsyncSession = Depends(session)) -> dict:
    user = await _consented(db, body, report_limiter)
    tipo, valor = normalize_value(body.tipo, body.valor)
    modalidad = body.modalidad if body.modalidad in MODALIDADES else None
    verificacion = UUID(body.verificacion_id) if body.verificacion_id else None
    indicador, nuevo = await banco.report(db, user, tipo, valor, modalidad, verificacion)
    return {"nuevo": nuevo, "valor": indicador.valor_visible, "nivel": indicador.nivel_riesgo,
            "personas": indicador.personas_distintas}


class RevisionIn(Persona):
    motivo: str = Field(..., min_length=3, max_length=300)


@router.post("/revision")
async def review(body: RevisionIn, db: AsyncSession = Depends(session)) -> dict:
    user = await _consented(db, body)
    if not user.telefono_hash:
        return {"estado": "falta_telefono"}
    solicitud = await banco.request_review(db, user, body.motivo)
    return {"estado": "en_revision"} if solicitud else {"estado": "sin_reportes"}


class InvitarIn(Persona):
    familiar: str = Field(..., min_length=2, max_length=60)
    relacion: str | None = None


@router.post("/circulo/invitar")
async def invite(body: InvitarIn, db: AsyncSession = Depends(session)) -> dict:
    user = await _consented(db, body)
    return {"token": await circulo.invite(db, user, body.familiar, body.relacion)}


@router.get("/circulo/invitacion/{token}")
async def invitation(token: str, db: AsyncSession = Depends(session)) -> dict:
    found = await circulo.pending_invite(db, token)
    if found is None:
        raise HTTPException(status_code=404, detail="La invitación no existe o ya se usó.")
    miembro, protegido = found
    return {"familiar": miembro.nombre, "protegido": protegido.nombre_corto or "Tu familiar"}


class AceptarIn(Persona):
    token: str
    acepta: bool


@router.post("/circulo/aceptar")
async def accept(body: AceptarIn, db: AsyncSession = Depends(session)) -> dict:
    user = await _user(db, body)
    usuarios.set_consent(user)  # accepting the Círculo is this person's consent
    found = await circulo.accept(db, body.token, user, body.acepta)
    if found is None:
        raise HTTPException(status_code=404, detail="La invitación no existe o ya se usó.")
    miembro, protegido = found
    return {"protegido_chat_id": usuarios.chat_id_of(protegido), "familiar": miembro.nombre, "acepta": body.acepta}


@router.post("/circulo/ver")
async def view_circle(persona: Persona, db: AsyncSession = Depends(session)) -> dict:
    user = await _user(db, persona)
    return {"miembros": [m.nombre for m, _ in await circulo.members(db, user)], "pendientes": await circulo.pending_names(db, user)}


class RespuestaIn(Persona):
    aviso_id: str
    respuesta: str = Field(..., pattern=r"^(si|no)$")


@router.post("/circulo/responder")
async def answer(body: RespuestaIn, db: AsyncSession = Depends(session)) -> dict:
    user = await _user(db, body)
    found = await circulo.answer(db, UUID(body.aviso_id), user, body.respuesta)
    if found is None:
        raise HTTPException(status_code=404, detail="Esa pregunta ya fue respondida o no es para ti.")
    _, miembro, protegido, others = found
    if body.respuesta == "no":
        await circulo.alert_all(db, protegido, tipo="alerta")
    return {"protegido_chat_id": usuarios.chat_id_of(protegido), "familiar": miembro.nombre, "respuesta": body.respuesta,
            "otros_chat_ids": [usuarios.chat_id_of(u) for _, u in others] if body.respuesta == "no" else []}


class AvisoIn(BaseModel):
    aviso_id: str


@router.post("/circulo/expirar")
async def expire(body: AvisoIn, db: AsyncSession = Depends(session)) -> dict:
    aviso = await circulo.expire_question(db, UUID(body.aviso_id))
    return {"expirado": aviso is not None}


@router.post("/circulo/salir")
async def leave(persona: Persona, db: AsyncSession = Depends(session)) -> dict:
    return {"eliminados": await circulo.leave(db, await _user(db, persona))}


@router.post("/borrar")
async def forget_me(persona: Persona, db: AsyncSession = Depends(session)) -> dict:
    """Ley 1581: the person can ask to delete their data at any time."""
    user = await usuarios.by_telegram(db, persona.telegram_id)
    if user:
        await circulo.leave(db, user)
        await db.execute(delete(Usuario).where(Usuario.id == user.id))
    return {"ok": True}
