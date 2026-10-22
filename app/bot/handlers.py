"""Conversation handlers: the 6-option menu, automatic detection and every flow of the guide.

The bot only talks to people and to the API. It keeps short-lived state in memory
(context.user_data): the current option, the last result for the kit and what can be reported.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from telegram import (
    InlineKeyboardButton as Btn,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.bot import textos
from app.bot.api import IMAGE_TIMEOUT, VOICE_TIMEOUT, Api, ApiError
from app.bot.formatters import (
    b, code, esc, format_analysis, format_call, format_code, format_heard, format_kit, format_not_connected, format_number, format_report,
    header, join,
)
from app.core.security import normalize_phone
from app.engine.enlaces import registered_domain
from app.engine.oficiales import official_websites
from app.engine.pistas import CHAT_LINKS, SHORTENERS, extract, plain
from app.schemas.contract import AnalysisResult

logger = logging.getLogger(__name__)

MD = ParseMode.MARKDOWN_V2
CIRCLE_TIMEOUT_SECONDS = 300
COLOMBIA = timezone(timedelta(hours=-5))
CALL_QUESTION = re.compile(r"(?i)\bme\s+est[aá]n?\s+llamando\b|\bme\s+llam(?:a|ó|o|aron|an)\b|\bes\s+real\s+(?:la|esta)\s+llamada\b")
CODE = re.compile(r"(?<!\d)(\d{4})(?!\d)")
YA_CAI = re.compile(r"(?i)\bya\s+ca[ií]\b|\bme\s+estafaron\b|\bquiero\s+denunciar\b")
GREETINGS = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "menu", "inicio", "empezar"}
THANKS = {"gracias", "muchas gracias", "ok", "listo", "vale", "perfecto", "dale"}


def _api(context: ContextTypes.DEFAULT_TYPE) -> Api:
    return context.application.bot_data["api"]


def _who(update: Update) -> dict:
    return {"telegram_id": update.effective_user.id, "chat_id": update.effective_chat.id, "nombre": update.effective_user.first_name}


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[Btn(f"{n} · {label}", callback_data=f"m{n}")] for n, label in textos.MENU_OPTIONS])


async def _reply(update: Update, text: str, **kwargs) -> None:
    await update.effective_message.reply_text(text, parse_mode=MD, **kwargs)


async def _send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, **kwargs) -> None:
    try:
        await context.bot.send_message(chat_id, text, parse_mode=MD, **kwargs)
    except TelegramError:
        logger.warning("Could not write to a Círculo member", exc_info=True)


async def _api_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: ApiError) -> None:
    if error.status == 403:
        context.user_data["consent"] = False
        await _ensure_consent(update, context)
    elif error.status == 429:
        await _reply(update, textos.DEMASIADO_RAPIDO)
    elif error.status in (404, 422) and error.detail:
        await _reply(update, esc(error.detail))
    else:
        await _reply(update, textos.SIN_RESPUESTA_API)


async def _ensure_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if context.user_data.get("consent"):
        return True
    try:
        info = await _api(context).post("/bot/inicio", json=_who(update))
    except ApiError:
        await _reply(update, textos.SIN_RESPUESTA_API)
        return False
    if info["consentimiento"]:
        context.user_data["consent"] = True
        return True
    await _reply(update, textos.CONSENTIMIENTO, reply_markup=InlineKeyboardMarkup([[Btn("Acepto", callback_data="consent")]]))
    return False


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["modo"] = None
    await _reply(update, textos.BIENVENIDA, reply_markup=_menu_keyboard())


# --- Commands -----------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args and context.args[0].startswith("c_"):
        await _circle_invitation(update, context, context.args[0][2:])
        return
    if await _ensure_consent(update, context):
        await show_menu(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, textos.AYUDA)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _ensure_consent(update, context):
        await show_menu(update, context)


async def circle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _ensure_consent(update, context):
        await _show_circle(update, context)


async def kit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_kit(update, context)


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_consent(update, context):
        return
    context.user_data["modo"] = "revision_motivo"
    await _reply(update, join(
        b("Revisión de tu número"),
        esc("Si tu número aparece reportado por error, cuéntame en una línea por qué. "
            "Primero te pediré compartir tu número, para saber que es tuyo."),
    ))


async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, join(
        b("¿Borrar tus datos?"),
        esc("Se borran tu número protegido, tu Círculo de Confianza y tus reportes. Lo que ya revisaste queda solo como dato anónimo."),
    ), reply_markup=InlineKeyboardMarkup([[Btn("Sí, borrar mis datos", callback_data="forget")]]))


# --- Messages -----------------------------------------------------------------------------

def _is_phone_only(text: str) -> bool:
    return len(text) <= 25 and re.fullmatch(r"[\d\s+().-]+", text) is not None and normalize_phone(text) is not None


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text:
        return
    if not await _ensure_consent(update, context):
        return
    simple = plain(text).strip(" ¡!¿?.")
    modo = context.user_data.get("modo")
    if simple in GREETINGS:
        await show_menu(update, context)
    elif simple in THANKS:
        await _reply(update, esc("¡Con gusto! Si te llega algo raro, envíamelo."))
    elif simple in {"1", "2", "3", "4", "5", "6"}:
        await _choose(update, context, simple)
    elif YA_CAI.search(text):
        await _choose(update, context, "6")
    elif modo == "circulo_nombre":
        await _ask_relative_phone(update, context, text)
    elif modo == "circulo_telefono":
        await _invite(update, context, context.user_data.get("familiar_nombre") or "tu familiar", text)
    elif modo == "revision_motivo":
        await _review(update, context, text)
    elif context.user_data.get("codigo_pendiente") and CODE.search(text) and len(text) <= 60:
        await _confirm_code(update, context, CODE.search(text).group(1))
    elif modo in ("llamada", "numero") and re.fullmatch(r"\d{4}", re.sub(r"\s", "", text)):
        await _confirm_code(update, context, re.sub(r"\s", "", text))
    elif modo == "llamada" or CALL_QUESTION.search(text):
        await _verified_call(update, context, text)
    elif _is_phone_only(text) or modo in ("numero", "reportar"):
        await _check_number(update, context, text)
    else:
        await _analyze_text(update, context, text, "compra" if modo == "compra" else "mensaje")


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.effective_message.contact
    if contact.user_id != update.effective_user.id:
        await _reply(update, esc("Comparte tu propio número con el botón, no el de otra persona."))
        return
    token = context.user_data.pop("invitacion_token", None)
    if token:  # accepting a Círculo invitation: the number proves who accepts
        await _accept_invitation(update, context, token, contact.phone_number)
        return
    try:
        await _api(context).post("/bot/telefono", json=_who(update) | {"telefono": contact.phone_number})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    await _reply(update, esc("Gracias, ya tengo tu número protegido."), reply_markup=ReplyKeyboardRemove())
    pending = context.user_data.pop("llamada_pendiente", None)
    code = context.user_data.pop("codigo_por_confirmar", None)
    if pending:
        await _verified_call(update, context, pending)
    elif code:
        await _confirm_code(update, context, code)
    elif context.user_data.get("modo") == "revision_motivo" and context.user_data.get("motivo_pendiente"):
        await _review(update, context, context.user_data.pop("motivo_pendiente"))


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_consent(update, context):
        return
    message = update.effective_message
    source = message.photo[-1] if message.photo else message.document
    await _reply(update, esc("Recibí tu captura. La estoy revisando…"))
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    data = bytes(await (await source.get_file()).download_as_bytearray())
    tipo = "compra" if context.user_data.get("modo") == "compra" else "mensaje"
    try:
        out = await _api(context).post("/bot/analizar-imagen", timeout=IMAGE_TIMEOUT,
                                       data={"telegram_id": update.effective_user.id, "chat_id": update.effective_chat.id, "tipo": tipo},
                                       files={"file": ("captura", data, "application/octet-stream")})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    await _deliver(update, context, out, out["resultado"].get("extracted_text") or "", tipo, fuente="captura")


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _ensure_consent(update, context):
        return
    message = update.effective_message
    source = message.voice or message.audio
    await _reply(update, esc("Escuchando tu nota de voz…"))
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    data = bytes(await (await source.get_file()).download_as_bytearray())
    try:
        out = await _api(context).post("/bot/analizar-voz", timeout=VOICE_TIMEOUT,
                                       data={"telegram_id": update.effective_user.id, "chat_id": update.effective_chat.id},
                                       files={"file": ("nota", data, "application/octet-stream")})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    heard = out["resultado"].get("extracted_text") or ""
    await _deliver(update, context, out, heard, "llamada", heard=heard, fuente="voz")


async def on_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, textos.NO_SOPORTADO, reply_markup=_menu_keyboard())


# --- Analysis -----------------------------------------------------------------------------

def _forwarded_from(update: Update) -> int | None:
    origin = getattr(update.effective_message, "forward_origin", None)
    user = getattr(origin, "sender_user", None)
    return user.id if user else None


async def _analyze_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, tipo: str) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    body = _who(update) | {"texto": text, "tipo": tipo, "reenviado_de": _forwarded_from(update)}
    try:
        out = await _api(context).post("/bot/analizar", json=body)
    except ApiError as error:
        await _api_error(update, context, error)
        return
    await _deliver(update, context, out, text, tipo)


def _remember(context: ContextTypes.DEFAULT_TYPE, result: AnalysisResult, text: str, fuente: str = "texto") -> list[tuple[str, str]]:
    found = extract(text)
    reportables = [("telefono", v) for v in found.telefonos] + [("llave", v) for v in found.llaves] + [("cuenta", v) for v in found.cuentas]
    # Links too, by their domain, but never a shortener, a chat link or an official site: that would brand a real service.
    official = {site for sites in official_websites().values() for site in sites}
    enlaces = []
    for url in found.urls:
        host = (urlsplit(url).hostname or "").removeprefix("www.")
        domain = registered_domain(host)
        if domain in official:
            continue
        enlaces.append(url)
        if host not in SHORTENERS | CHAT_LINKS and ("enlace", domain) not in reportables:
            reportables.append(("enlace", domain))
    context.user_data["reportables"] = reportables[:5]
    context.user_data["reportar_modalidad"] = result.modalidad
    context.user_data["ultima_verificacion"] = result.verification_id
    now = datetime.now(COLOMBIA)
    context.user_data["ultimo"] = {
        "texto": text[:600], "nivel": result.risk_level.value, "puntaje": result.risk_score, "categoria": result.category,
        "dia": f"{now:%d/%m/%Y}", "hora": f"{now.hour % 12 or 12}:{now:%M} {'a. m.' if now.hour < 12 else 'p. m.'}",
        "fuente": fuente, "enlaces": enlaces[:5], "datos": reportables[:8],
        "motivos": list(dict.fromkeys(s.label for s in result.signals if s.points > 0))[:3],
        "referencia": f"DSM-{result.verification_id.replace('-', '')[:8].upper()}" if result.verification_id else None,
    }
    return reportables


async def _deliver(update: Update, context: ContextTypes.DEFAULT_TYPE, out: dict, text: str, tipo: str, heard: str | None = None,
                   fuente: str = "texto") -> None:
    result = AnalysisResult.model_validate(out["resultado"])
    reportables = _remember(context, result, text, fuente)
    questions = out.get("preguntas_circulo") or []
    if questions:
        await _ask_circle(update, context, questions, text, result)
        return
    message = format_analysis(result)
    if heard:
        message = join(format_heard(heard), "", message)
    buttons = []
    if result.risk_level.value in ("high", "medium"):
        if reportables:
            buttons.append(Btn("Reportar", callback_data="rep"))
        buttons.append(Btn("Kit de denuncia", callback_data="kit"))
    if tipo == "compra":
        buttons.append(Btn("¿Cómo compro seguro?", callback_data="seguro"))
    await _reply(update, message, reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None)

    name = update.effective_user.first_name or "Tu familiar"
    for chat_id in out.get("avisar_familiares") or []:
        await _send(context, chat_id, join(
            f"🔴 {b('AVISO DE TU CÍRCULO')}",
            f"{b(name)} {esc('acaba de revisar un mensaje de')} {b('alto riesgo')}" + (f" {esc('(' + result.category + ')')}" if result.category else "") + esc("."),
            esc("Puede ser un buen momento para llamarle y acompañarle."),
        ))


# --- Círculo de Confianza ------------------------------------------------------------------

async def _ask_circle(update: Update, context: ContextTypes.DEFAULT_TYPE, questions: list[dict], text: str,
                      result: AnalysisResult | None = None) -> None:
    names = sorted({q["nombre"] for q in questions})
    words = set(re.findall(r"\w+", plain(text)))
    mentioned = [n for n in names if plain(n).split()[0] in words]
    who = ", ".join(names)
    await _reply(update, join(
        header(result.risk_level.value, result.risk_score, result.category) if result else f"🟡 {b('SOSPECHOSO')}",
        (f"{esc('Dice ser')} {b(mentioned[0])}{esc(', que está en tu Círculo.')}" if mentioned
         else esc("Tiene el patrón del falso familiar: alguien que dice ser de tu familia y pide dinero.")),
        esc(f"Le estoy preguntando a {who} en su Telegram."),
        b("Mientras tanto, no transfieras."),
        esc("Con IA se puede clonar la voz: si te llaman, pregunta la palabra clave que acordaron en familia."),
    ))
    protegido = update.effective_user.first_name or "Tu familiar"
    for q in questions:
        await _send(context, q["chat_id"], join(
            f"{b(q['nombre'])}{esc(':')} {b(protegido)} {esc('recibió un mensaje de alguien que dice ser de la familia y pide dinero o ayuda urgente.')}",
            b("¿Fuiste tú?"),
        ), reply_markup=InlineKeyboardMarkup([[
            Btn("Sí, fui yo", callback_data=f"resp:{q['aviso_id']}:si"),
            Btn("No fui yo", callback_data=f"resp:{q['aviso_id']}:no"),
        ]]))
        context.job_queue.run_once(_circle_timeout, CIRCLE_TIMEOUT_SECONDS, name=f"aviso:{q['aviso_id']}",
                                   data={"aviso_id": q["aviso_id"], "chat_id": update.effective_chat.id, "nombre": q["nombre"]})


async def _circle_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    try:
        expired = (await _api(context).post("/bot/circulo/expirar", json={"aviso_id": data["aviso_id"]}))["expirado"]
    except ApiError:
        return
    if expired:
        name = data["nombre"]
        await _send(context, data["chat_id"], join(
            f"🟡 {b('NO PUDIMOS CONFIRMARLO')}",
            esc(f"{name} no respondió en 5 minutos."),
            f"{b('No transfieras.')} {esc(f'Llama a {name} a su número de siempre.')}",
        ))


async def _show_circle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        info = await _api(context).post("/bot/circulo/ver", json=_who(update))
    except ApiError as error:
        await _api_error(update, context, error)
        return
    lines = [b("Mi Círculo de Confianza")]
    lines.append(esc("Miembros: " + ", ".join(info["miembros"])) if info["miembros"] else esc("Todavía no tienes familiares en tu Círculo."))
    if info["pendientes"]:
        lines.append(esc("Invitaciones sin aceptar: " + ", ".join(info["pendientes"])))
    waiting = info.get("por_aprobar") or []
    if waiting:
        lines.append(f"{b('Esperan tu confirmación:')} {esc(', '.join(m['nombre'] for m in waiting))}")
    lines.append(esc("Si alguien te escribe diciendo ser de tu familia, le preguntaré al familiar real antes de que hagas algo."))
    buttons = [[Btn(f"Sí, es {m['nombre']}", callback_data=f"apr:{m['id']}:1"), Btn("No lo conozco", callback_data=f"apr:{m['id']}:0")]
               for m in waiting]
    buttons.append([Btn("Agregar familiar", callback_data="c_add")])
    if info["miembros"] or info["pendientes"]:
        buttons.append([Btn("Salir del Círculo", callback_data="c_leave")])
    await _reply(update, join(*lines), reply_markup=InlineKeyboardMarkup(buttons))


async def _ask_relative_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> None:
    """The relative's number goes with the invitation: only the person with that number can accept it."""
    context.user_data["familiar_nombre"] = name.strip()[:60]
    context.user_data["modo"] = "circulo_telefono"
    await _reply(update, join(
        f"{esc('¿Cuál es el número de celular de')} {b(name.strip()[:60])}{esc('?')}",
        esc("Así compruebo que quien acepte la invitación sea de verdad esa persona, y no alguien que recibió el enlace."),
    ))


async def _invite(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str, phone: str) -> None:
    if normalize_phone(phone) is None:
        await _reply(update, esc("No reconocí ese número. Escríbelo con todos sus dígitos, por ejemplo 310 000 0000."))
        return
    try:
        out = await _api(context).post("/bot/circulo/invitar", json=_who(update) | {"familiar": name[:60], "telefono": phone})
    except ApiError as error:
        if error.status == 422:  # their own number, or one that does not read as a phone
            await _reply(update, esc(error.detail))
            return
        await _api_error(update, context, error)
        return
    context.user_data["modo"] = None
    context.user_data.pop("familiar_nombre", None)
    link = f"https://t.me/{context.bot.username}?start=c_{out['token']}"
    await _reply(update, join(
        f"{esc('Listo. Reenvíale este enlace a')} {b(name)}{esc(':')}",
        esc(link),
        esc(f"Vence en {out['vence_en_horas']} horas y sirve una sola vez."),
        f"{b('Validación:')} {esc(f'para aceptar, {name} tendrá que compartir su número')} {code(out['telefono'])} "
        f"{esc('y después tú confirmarás que es tu familiar. Si alguien más abre el enlace, no podrá entrar.')}",
    ))


async def _circle_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    try:
        info = await _api(context).get(f"/bot/circulo/invitacion/{token}")
    except ApiError as error:
        await _api_error(update, context, error)
        return
    context.user_data["invitacion"] = info
    await _reply(update, join(
        f"{esc('Hola,')} {b(update.effective_user.first_name or info['familiar'])}{esc('.')} "
        f"{b(info['protegido'])} {esc('te agregó a su')} {b('Círculo de Confianza')}{esc('.')}",
        esc("Si alguien le escribe diciendo ser tú, te preguntaré a ti antes de que haga algo. Tus datos se guardan protegidos (Ley 1581)."),
        esc(f"Para confirmar que eres tú, te pediré tu número y {info['protegido']} confirmará que te conoce."),
        b("¿Aceptas?"),
    ), reply_markup=InlineKeyboardMarkup([[Btn("Sí, acepto", callback_data=f"acc:{token}:1"), Btn("No", callback_data=f"acc:{token}:0")]]))


# --- Llamada Verificada, numbers and reports -------------------------------------------------

async def _verified_call(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    context.user_data["modo"] = None
    try:
        info = await _api(context).post("/bot/llamada", json=_who(update) | {"texto": text})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    if info["estado"] == "no_conectada":
        context.user_data["modo"] = "numero"
        await _reply(update, format_not_connected(info))
    elif info["estado"] == "entidad_desconocida":
        context.user_data["modo"] = "numero"
        buttons = [[Btn(f"📞 {name}", callback_data=f"ent:{name}"[:64])] for name in info["entidades"][:8]]
        await _reply(update, join(
            esc("No encontré esa entidad en Llamada Verificada."),
            esc("Toca la entidad que dice llamarte:") if buttons else esc("Todavía no hay entidades conectadas."),
            esc("Si no está, envíame el número que te llamó y lo reviso en el Banco de números."),
            f"{b('Regla de oro:')} {esc('cuelga y llama tú a la línea oficial que está en tu tarjeta.')}",
        ), reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)
    elif info["estado"] == "falta_telefono":
        context.user_data["llamada_pendiente"] = text
        await _reply(update, textos.PEDIR_TELEFONO, reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Compartir mi número", request_contact=True)]], one_time_keyboard=True, resize_keyboard=True))
    elif info["estado"] == "real":
        context.user_data["codigo_pendiente"] = True
        await _reply(update, format_call(info))
    else:
        context.user_data["modo"] = "reportar"
        context.user_data["reportar_modalidad"] = "falso_asesor"
        await _reply(update, format_call(info))


async def _confirm_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str) -> None:
    context.user_data["codigo_pendiente"] = False
    context.user_data["modo"] = None
    try:
        info = await _api(context).post("/bot/llamada/confirmar", json=_who(update) | {"codigo": code})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    if info["estado"] == "falta_telefono":
        context.user_data["codigo_por_confirmar"] = code
        await _reply(update, textos.PEDIR_TELEFONO, reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Compartir mi número", request_contact=True)]], one_time_keyboard=True, resize_keyboard=True))
        return
    await _reply(update, format_code(info))


async def _entity_buttons(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup | None:
    """One button per entity in Llamada Verificada: tapping beats typing the name right."""
    try:
        names = (await _api(context).get("/bot/entidades"))["entidades"]
    except ApiError:
        return None
    buttons = [[Btn(f"📞 {name}", callback_data=f"ent:{name}"[:64])] for name in names[:8]]
    return InlineKeyboardMarkup(buttons) if buttons else None


async def _check_number(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    reporting = context.user_data.get("modo") == "reportar"
    context.user_data["modo"] = None
    if normalize_phone(text) is None:
        await _reply(update, esc("No reconocí un número de teléfono. Pégalo con todos sus dígitos, por ejemplo 310 000 0000."))
        return
    try:
        if reporting:
            info = await _api(context).post("/bot/reportar", json=_who(update) | {
                "valor": text, "tipo": "telefono", "modalidad": context.user_data.get("reportar_modalidad")})
            await _reply(update, format_report([info]))
            return
        info = await _api(context).post("/bot/numero", json=_who(update) | {"valor": text, "tipo": "telefono"})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    context.user_data["reportables"] = [("telefono", text)]
    context.user_data["reportar_modalidad"] = None
    keyboard = None if info.get("oficial_de") else InlineKeyboardMarkup([[Btn("Reportar este número", callback_data="rep")]])
    await _reply(update, format_number(info), reply_markup=keyboard)


async def _report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = context.user_data.get("reportables") or []
    if not items:
        await _reply(update, esc("No encontré números, llaves ni cuentas para reportar en lo último que revisamos."))
        return
    context.user_data["reportables"] = []  # a second tap while this runs finds nothing left to send twice
    reports = []
    for tipo, valor in items:
        try:
            reports.append(await _api(context).post("/bot/reportar", json=_who(update) | {
                "valor": valor, "tipo": tipo, "modalidad": context.user_data.get("reportar_modalidad"),
                "verificacion_id": context.user_data.get("ultima_verificacion")}))
        except ApiError as error:
            context.user_data["reportables"] = items[len(reports):]
            await _api_error(update, context, error)
            return
    last = context.user_data.get("ultimo")
    from_last = last is not None and all(item in last["datos"] for item in items)
    if from_last:
        last["reportado"] = True
    await _reply(update, format_report(reports),
                 reply_markup=InlineKeyboardMarkup([[Btn("Kit de denuncia", callback_data="kit")]]) if from_last else None)


async def _review(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str) -> None:
    try:
        info = await _api(context).post("/bot/revision", json=_who(update) | {"motivo": reason[:300]})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    if info["estado"] == "falta_telefono":
        context.user_data["motivo_pendiente"] = reason
        await _reply(update, esc("Para saber que el número es tuyo, compártelo con el botón."), reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Compartir mi número", request_contact=True)]], one_time_keyboard=True, resize_keyboard=True))
        return
    context.user_data["modo"] = None
    if info["estado"] == "en_revision":
        await _reply(update, join(
            f"{esc('Tu número quedó')} {b('en revisión')}{esc('. Una persona del equipo lo revisará.')}",
            esc("Mientras tanto, a quien pregunte le diremos que está en revisión, no que es una estafa."),
        ))
    else:
        await _reply(update, esc("Tu número no tiene reportes: no hay nada que revisar."))


# --- Kit and "Ya caí" ---------------------------------------------------------------------

async def _send_kit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last = context.user_data.get("ultimo")
    if not last:
        await _reply(update, esc("Primero envíame el mensaje, la captura o el número que quieres denunciar y te armo el kit."))
        return
    await _reply(update, format_kit(last, textos.LINEAS_DENUNCIA))


async def _ya_cai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, textos.YA_CAI, reply_markup=InlineKeyboardMarkup([
        [Btn("Una clave o un código", callback_data="yc_codigo")],
        [Btn("Datos de mi tarjeta", callback_data="yc_tarjeta")],
        [Btn("Dinero", callback_data="yc_dinero")],
        [Btn("Datos personales", callback_data="yc_datos")],
        [Btn("Quiero denunciar: kit de denuncia", callback_data="kit")],
    ]))


async def _choose(update: Update, context: ContextTypes.DEFAULT_TYPE, option: str) -> None:
    context.user_data["modo"] = {"1": "mensaje", "2": "llamada", "3": "numero", "5": "compra"}.get(option)
    if option == "1":
        await _reply(update, textos.PEDIR_MENSAJE)
    elif option == "2":
        await _reply(update, textos.PEDIR_ENTIDAD, reply_markup=await _entity_buttons(context))
    elif option == "3":
        await _reply(update, textos.PEDIR_NUMERO)
    elif option == "4":
        await _show_circle(update, context)
    elif option == "5":
        await _reply(update, textos.ANTES_DE_PAGAR)
    else:
        await _ya_cai(update, context)


# --- Buttons ------------------------------------------------------------------------------

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError:  # the tap waited too long for Telegram to accept the answer: still do what was asked
        logger.info("Late button answer")
    data = query.data or ""
    logger.info("Button %s", data.split(":", 1)[0])  # never the token after ":"
    if data == "consent":
        try:
            await _api(context).post("/bot/consentimiento", json=_who(update))
        except ApiError as error:
            await _api_error(update, context, error)
            return
        context.user_data["consent"] = True
        await query.edit_message_reply_markup(None)
        await show_menu(update, context)
    elif data.startswith("acc:"):
        await _answer_invitation(update, context, data)
    elif data.startswith("apr:"):
        await _approve(update, context, data)
    elif data.startswith("ent:"):
        if await _ensure_consent(update, context):
            await _verified_call(update, context, data[4:])
    elif data.startswith("resp:"):
        await _answer_question(update, context, data)
    elif not await _ensure_consent(update, context):
        return
    elif data.startswith("m") and data[1:] in {"1", "2", "3", "4", "5", "6"}:
        await _choose(update, context, data[1:])
    elif data.startswith("yc_"):
        steps = textos.YA_CAI_PASOS.get(data[3:], [])
        await _reply(update, join(
            f"🔴 {b(textos.YA_CAI_TITULOS.get(data[3:], 'Calma, vamos paso a paso'))}",
            *[esc(f"{n}. {step}") for n, step in enumerate(steps, 1)],
            esc("Cuando puedas, toca «Kit de denuncia»: te armo un resumen para enviar."),
        ), reply_markup=InlineKeyboardMarkup([[Btn("Kit de denuncia", callback_data="kit")]]))
    elif data == "kit":
        await _send_kit(update, context)
    elif data == "rep":
        await _report(update, context)
    elif data == "seguro":
        await _reply(update, textos.COMPRA_SEGURA, reply_markup=InlineKeyboardMarkup([[Btn("Reportar", callback_data="rep")]]))
    elif data == "c_add":
        context.user_data["modo"] = "circulo_nombre"
        await _reply(update, textos.PEDIR_FAMILIAR)
    elif data == "c_leave":
        await _api(context).post("/bot/circulo/salir", json=_who(update))
        await _reply(update, esc("Listo. Saliste del Círculo de Confianza."))
    elif data == "forget":
        await _api(context).post("/bot/borrar", json=_who(update))
        context.user_data.clear()
        await query.edit_message_reply_markup(None)
        await _reply(update, esc("Listo, borré tus datos. Si vuelves a escribirme, te pediré permiso de nuevo."))


async def _answer_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    _, token, accepted = data.split(":")
    await update.callback_query.edit_message_reply_markup(None)
    if accepted == "1":  # first the number, shared with Telegram's button: only then the API hears of it
        context.user_data["invitacion_token"] = token
        await _reply(update, join(
            f"{esc('Para confirmar que eres tú, toca')} {b('Compartir mi número')}{esc('.')}",
            esc("Solo lo uso para esta validación y lo guardo protegido."),
        ), reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Compartir mi número", request_contact=True)]],
                                            one_time_keyboard=True, resize_keyboard=True))
        return
    try:
        info = await _api(context).post("/bot/circulo/aceptar", json=_who(update) | {"token": token, "acepta": False})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    context.user_data.pop("invitacion", None)
    await _reply(update, esc("Listo, no te agregué al Círculo."))
    await _send(context, info["protegido_chat_id"], esc(f"{info['familiar']} no aceptó la invitación a tu Círculo."))


async def _accept_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str, phone: str) -> None:
    try:
        info = await _api(context).post("/bot/circulo/aceptar", json=_who(update) | {"token": token, "acepta": True, "telefono": phone})
    except ApiError as error:
        if error.status == 404:
            await _reply(update, esc("Esa invitación ya se usó o venció (dura 48 horas). Pídele a tu familiar que te invite de nuevo."),
                         reply_markup=ReplyKeyboardRemove())
            return
        await _api_error(update, context, error)
        return
    context.user_data.pop("invitacion", None)
    protegido, familiar = info["protegido"], info["familiar"]
    if info["estado"] == "por_aprobar":
        context.user_data["consent"] = True
        await _reply(update, esc(f"Gracias: tu número coincide. Le pedí a {protegido} que confirme que eres tú; te aviso apenas lo haga."),
                     reply_markup=ReplyKeyboardRemove())
        await _send(context, info["protegido_chat_id"], join(
            f"🔐 {b('VALIDAR FAMILIAR')}",
            f"{b(familiar)} {esc('aceptó tu invitación desde el número')} {code(info['telefono'])}{esc(', el mismo que me diste.')}",
            b(f"¿Es de verdad {familiar}?"),
        ), reply_markup=InlineKeyboardMarkup([[Btn(f"Sí, es {familiar}", callback_data=f"apr:{info['miembro_id']}:1"),
                                               Btn("No lo conozco", callback_data=f"apr:{info['miembro_id']}:0")]]))
    elif info["estado"] == "no_coincide":
        await _reply(update, join(
            f"🔴 {b('EL NÚMERO NO COINCIDE')}",
            esc(f"Ese no es el número que {protegido} me dio para esta invitación, así que no te agregué."),
            esc(f"Si es un error, pídele a {protegido} que te invite de nuevo con tu número."),
        ), reply_markup=ReplyKeyboardRemove())
        await _send(context, info["protegido_chat_id"], join(
            f"⚠️ {b('INTENTO DE ENTRAR A TU CÍRCULO')}",
            f"{esc('Alguien abrió tu invitación para')} {b(familiar)} {esc('con otro número')} {code(info['telefono'] or 'oculto')}{esc('.')}",
            esc(f"No lo agregué. La invitación sigue esperando a {familiar}. Si no le enviaste el enlace a nadie más, puede ser un intento de estafa."),
        ))
    else:  # an invitation from before the validation by number
        await _reply(update, esc(f"Esta invitación es anterior a la validación por número. Pídele a {protegido} que te invite de nuevo."),
                     reply_markup=ReplyKeyboardRemove())


async def _approve(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    _, miembro_id, accepted = data.split(":")
    try:
        info = await _api(context).post("/bot/circulo/aprobar", json=_who(update) | {"miembro_id": miembro_id, "aprueba": accepted == "1"})
    except ApiError as error:
        if error.status == 404:
            await _reply(update, esc("Esa solicitud ya no está pendiente."))
            return
        await _api_error(update, context, error)
        return
    await update.callback_query.edit_message_reply_markup(None)
    name = update.effective_user.first_name or "Tu familiar"
    if info["aprueba"]:
        await _reply(update, f"✅ {esc('Listo:')} {b(info['familiar'])} {esc('ya está en tu Círculo de Confianza, validado.')}")
        await _send(context, info["familiar_chat_id"], f"✅ {b(name)} {esc('confirmó que eres tú: ya estás en su Círculo de Confianza.')}")
    else:
        await _reply(update, esc("Listo, no quedó en tu Círculo. Si alguien insiste en hacerse pasar por tu familiar, puede ser un intento de estafa."))
        await _send(context, info["familiar_chat_id"], esc(f"{name} no confirmó la invitación, así que no quedaste en su Círculo."))


async def _answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    _, aviso_id, answer = data.split(":")
    try:
        info = await _api(context).post("/bot/circulo/responder", json=_who(update) | {"aviso_id": aviso_id, "respuesta": answer})
    except ApiError as error:
        await _api_error(update, context, error)
        return
    for job in context.job_queue.get_jobs_by_name(f"aviso:{aviso_id}"):
        job.schedule_removal()
    await update.callback_query.edit_message_reply_markup(None)
    await _reply(update, esc("Gracias. Ya le aviso a tu familiar."))
    name = info["familiar"]
    if answer == "no":
        await _send(context, info["protegido_chat_id"], join(
            f"🔴 {b('ES UNA ESTAFA')}",
            b(f"{name} confirmó que NO fue quien te escribió."),
            esc("No transfieras y bloquea ese número."),
            esc("¿Quieres reportarlo? Envíame el número."),
        ))
        for chat_id in info["otros_chat_ids"]:
            await _send(context, chat_id, join(
                f"🔴 {b('ALERTA DE TU CÍRCULO')}",
                esc(f"A alguien de tu Círculo le llegó hoy un mensaje falso de una persona que decía ser {name}."),
                f"{esc('Si a ti te llega algo parecido,')} {b('no caigas')}{esc('.')}",
            ))
    else:
        await _send(context, info["protegido_chat_id"], join(
            f"🟢 {b(f'{name} confirmó que sí fue quien te escribió.')}",
            esc(f"Aun así, si te pide dinero, llama a {name} a su número de siempre antes de transferir."),
        ))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Without this, a failed handler leaves the person with no answer at all."""
    logger.error("Bot handler failed", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(textos.SIN_RESPUESTA_API, parse_mode=MD)
        except TelegramError:
            pass
