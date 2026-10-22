import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import BadRequest

from app.bot import client, handlers, textos
from app.bot.formatters import (
    block, format_analysis, format_call, format_code, format_heard, format_kit, format_not_connected, format_number, format_report,
    relato,
)
from app.schemas.contract import AnalysisResult, SignalItem, SignalSource

# MarkdownV2 reserved characters, except "*" and "_", which the formatters use as markup.
RESERVED = set("[]()~`>#+-=|{}.!")


def unescaped_reserved(message: str) -> list[str]:
    found = []
    i = 0
    while i < len(message):
        if message[i] == "\\":
            i += 2
            continue
        if message[i] == "`":  # inline code: its content follows other rules
            end = message.find("`", i + 1)
            assert end != -1, message
            i = end + 1
            continue
        if message[i] in RESERVED:
            found.append(message[i])
        i += 1
    return found


def assert_valid_markdown(message: str) -> None:
    assert unescaped_reserved(message) == [], message
    unescaped = message.replace("\\*", "").replace("\\_", "")
    assert unescaped.count("*") % 2 == 0 and unescaped.count("_") % 2 == 0, message


def result(level="high", score=96, summary="Es muy probable que sea una estafa.", **kwargs) -> AnalysisResult:
    return AnalysisResult(risk_level=level, risk_score=score, summary=summary, **kwargs)


KIT = {"nivel": "high", "puntaje": 100, "categoria": "Posible cobranza falsa", "dia": "21/10/2026", "hora": "10:48 p. m.",
       "motivos": ["Pide pagar o escribir por un canal que vino en el mismo mensaje.", "Usa urgencia, amenazas o premios."],
       "fuente": "captura", "referencia": "DSM-1A2B3C4D", "texto": "Systemgroup y Credivalores…",
       "datos": [("telefono", "576017560385"), ("telefono", "573044722062"), ("enlace", "systemgroup.info")],
       "enlaces": ["https://systemgroup.info", "https://wa.me/+573044722062"]}

SIGNAL = SignalItem(code="ENLACE_IMITA_OFICIAL", label="El enlace no es la página oficial de BancoAndino.",
                    evidence="bancoandino-seguro.co", source=SignalSource.ENLACES, points=30)


@pytest.mark.parametrize("message", [
    format_analysis(result(signals=[SIGNAL], category="Suplantación de entidad", recommendations=["No abras el enlace (ni pagues)."])),
    format_analysis(result("inconclusive", 0)),
    format_analysis(result("low", 0, summary="No encontramos señales de estafa.")),
    format_heard("Me llamaron del banco... y me pidieron el código (urgente)!"),
    format_call({"estado": "real", "entidad": "BancoAndino", "motivo": "Confirmar una compra.", "codigo": "4821"}),
    format_call({"estado": "no_registrada", "entidad": "BancoAndino", "lineas_oficiales": ["+57 601 000 0002"]}),
    format_code({"estado": "correcto", "entidad": "BancoAndino"}),
    format_not_connected({"estado": "no_conectada", "entidad": "Bancolombia", "sitio": "bancolombia.com"}),
    format_not_connected({"estado": "no_conectada", "entidad": "Bancolombia", "sitio": "bancolombia.com", "linea": "01 8000 9 12345"}),
    format_number({"encontrado": True, "valor": "(601) 343 0000", "oficial_de": "Bancolombia", "sitio": "bancolombia.com", "nivel": 0}),
    format_code({"estado": "incorrecto"}),
    format_number({"encontrado": True, "valor": "+57 601 ••• 0000", "nivel": 90, "personas": 29, "reportes": 37,
                   "modalidad": "Falso asesor del banco", "estado": "normal", "oficial_de": None}),
    format_number({"encontrado": True, "valor": "+57 601 ••• 0002", "oficial_de": "BancoAndino", "nivel": 0}),
    format_number({"encontrado": False}),
    format_number({"encontrado": True, "estado": "en_revision", "nivel": 40, "personas": 2, "reportes": 2}),
    format_report([{"nuevo": True, "valor": "+57 320 ••• 1234", "personas": 3}]),
    format_report([{"nuevo": True, "valor": "systemgroup.info", "personas": 1}, {"nuevo": False, "valor": "+57 320 ••• 1234", "personas": 2}]),
    format_report([{"nuevo": False, "valor": "+57 320 ••• 1234", "personas": 2}]),
    format_kit(KIT, textos.LINEAS_DENUNCIA),
    format_kit(KIT | {"fuente": "texto", "referencia": None, "reportado": True}, textos.LINEAS_DENUNCIA),
    *[value for name, value in vars(textos).items() if name.isupper() and isinstance(value, str)],
])
def test_every_message_is_valid_markdown_v2(message):
    assert_valid_markdown(message)


def test_analysis_leads_with_the_semaforo_and_says_what_to_do():
    message = format_analysis(result(signals=[SIGNAL], category="Suplantación de entidad", recommendations=["No abras el enlace."]))
    first, *rest = message.split("\n")
    assert first.startswith("🔴 *ALTO RIESGO · 96/100*") and "Qué hacer:" in message and len(message.split("\n")) <= 10


def test_counts_of_one_read_well():
    number = format_number({"encontrado": True, "valor": "+57 320 ••• 1234", "nivel": 72, "personas": 1, "reportes": 1, "estado": "normal"})
    assert "*1 reporte* de 1 persona\\." in number
    assert "1 persona lo reportó" in format_report([{"nuevo": True, "valor": "+57 320 ••• 1234", "personas": 1}])
    assert "3 personas lo reportaron" in format_report([{"nuevo": True, "valor": "+57 320 ••• 1234", "personas": 3}])


def test_a_bank_that_has_not_joined_is_never_called_false():
    message = format_not_connected({"estado": "no_conectada", "entidad": "Bancolombia", "sitio": "bancolombia.com"})
    assert message.startswith("🟡 *NO PUEDO CONFIRMARLO*") and "bancolombia\\.com" in message and "NO ES TU BANCO" not in message


def test_a_published_line_tells_where_to_call_but_not_that_a_call_is_real():
    message = format_number({"encontrado": True, "valor": "(601) 343 0000", "oficial_de": "Bancolombia", "sitio": "bancolombia.com", "nivel": 0})
    assert message.startswith("🟢 *LÍNEA OFICIAL · PUEDES CONTESTAR*") and "se puede falsificar" in message and "bancolombia\\.com" in message
    call = format_not_connected({"estado": "no_conectada", "entidad": "Bancolombia", "linea": "01 8000 9 12345"})
    assert "01 8000 9 12345" in call


def test_links_can_be_reported_but_never_a_shortener_a_chat_or_an_official_site():
    context = SimpleNamespace(user_data={})
    text = "Paga hoy en https://bit.ly/x o en .cuctly.cc/pago, escríbenos a wa.me/573001112233 o mira bancolombia.com"
    reportables = handlers._remember(context, result("high", 80), text)
    assert ("enlace", "cuctly.cc") in reportables
    assert not any(valor in ("bit.ly", "wa.me", "bancolombia.com") for _, valor in reportables)


def test_the_kit_is_ready_for_the_police():
    kit = format_kit(KIT, textos.LINEAS_DENUNCIA)
    assert kit.startswith("📋 *KIT DE DENUNCIA*") and "DSM\\-1A2B3C4D" in kit
    assert "`+57 601 756 0385`" in kit and "`+57 304 472 2062`" in kit
    # Links in a box, so that nobody opens them by mistake; a screenshot is attached, not its OCR text.
    assert "`https://wa.me/+573044722062`" in kit and "Systemgroup y Credivalores" not in kit and "adjunta la captura original" in kit
    assert "adenunciar\\.policia\\.gov\\.co" in kit
    typed = format_kit(KIT | {"fuente": "texto", "texto": "Hola,\n\n  paga  hoy"}, textos.LINEAS_DENUNCIA)
    assert "El mensaje dice: «Hola, paga hoy»." in typed


def test_the_account_of_the_facts_uses_only_what_was_analysed():
    text = relato(KIT)
    assert text.startswith("El 21/10/2026, a las 10:48 p. m., revisé en Desenmascara un mensaje que recibí, "
                           "que identificó como «Posible cobranza falsa». Anexo la captura de pantalla.")
    assert ("En el mensaje aparecen los teléfonos +57 601 756 0385 y +57 304 472 2062, "
            "y los enlaces https://systemgroup.info y https://wa.me/+573044722062.") in text
    assert text.endswith("como alto riesgo (100/100) por estas señales: pide pagar o escribir por un canal que vino "
                         "en el mismo mensaje; usa urgencia, amenazas o premios.")
    # Nothing it cannot know: no amount, no "perdí", no bank name that was not in the message.
    assert "$" not in text and "perd" not in text
    call = relato(KIT | {"fuente": "voz", "texto": "Dijeron ser del banco", "datos": [], "enlaces": []})
    assert "conté en Desenmascara una llamada que recibí" in call and "Lo que me dijeron: «Dijeron ser del banco»." in call
    # In a box with a «Copiar» button; the backtick of a message cannot close it early.
    assert "```\nEl 21/10/2026" in format_kit(KIT, textos.LINEAS_DENUNCIA)
    assert "\\`" in block("a`b")


def test_reporting_answers_with_what_went_into_the_banco():
    api = FakeApi({"/bot/reportar": lambda body: {"nuevo": True, "valor": body["valor"], "personas": 2}})
    update, context = fake(None, api)
    reportables = handlers._remember(context, result("high", 90), "Paga en systemgroup.info o al 304 472 2062")
    asyncio.run(handlers._report(update, context))
    message, = replies(update)
    assert message.startswith("✅ *REPORTE RECIBIDO*") and "2 personas lo reportaron" in message
    assert [body["valor"] for _, body in api.calls] == [valor for _, valor in reportables]
    assert context.user_data["ultimo"]["reportado"] and context.user_data["reportables"] == []


def test_a_late_button_tap_still_does_what_was_asked():
    update, context = fake(None, FakeApi({}))
    update.callback_query = SimpleNamespace(data="kit", answer=AsyncMock(side_effect=BadRequest("Query is too old")))
    asyncio.run(handlers.on_button(update, context))
    assert "Primero envíame" in replies(update)[0]


def test_the_same_reason_is_said_once():
    twice = SignalItem(code="DOMINIO_NO_REGISTRADO", label="El enlace lleva a una página que no aparece registrada.",
                       evidence="a.co", source=SignalSource.ENLACES, points=15)
    message = format_analysis(result(signals=[twice, twice.model_copy(update={"evidence": "b.co"})]))
    assert message.count("no aparece registrada") == 1


def test_verified_call_code_is_in_a_box():
    assert "`4 8 2 1`" in format_call({"estado": "real", "entidad": "BancoAndino", "motivo": "Confirmar una compra.", "codigo": "4821"})


def fake_bot(name, short, description, photos):
    return SimpleNamespace(
        id=1, get_my_name=AsyncMock(return_value=SimpleNamespace(name=name)),
        get_my_short_description=AsyncMock(return_value=SimpleNamespace(short_description=short)),
        get_my_description=AsyncMock(return_value=SimpleNamespace(description=description)),
        get_user_profile_photos=AsyncMock(return_value=SimpleNamespace(total_count=photos)),
        set_my_name=AsyncMock(), set_my_short_description=AsyncMock(), set_my_description=AsyncMock(), set_my_profile_photo=AsyncMock(),
    )


def test_profile_sends_only_what_changed():
    assert len(client.NOMBRE) <= 64 and len(client.DESCRIPCION_CORTA) <= 120 and len(client.DESCRIPCION) <= 512  # Telegram's limits
    bot = fake_bot(client.NOMBRE, "vieja", client.DESCRIPCION, photos=1)
    asyncio.run(client._profile(bot))
    bot.set_my_short_description.assert_awaited_once_with(client.DESCRIPCION_CORTA)
    for setter in (bot.set_my_name, bot.set_my_description, bot.set_my_profile_photo):
        setter.assert_not_awaited()

    new = fake_bot("Desenmascara Demo", client.DESCRIPCION_CORTA, client.DESCRIPCION, photos=0)
    asyncio.run(client._profile(new))
    new.set_my_name.assert_awaited_once_with(client.NOMBRE)
    new.set_my_profile_photo.assert_awaited_once()


# --- Handlers with fake Telegram and API objects ------------------------------------------------

class FakeApi:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def post(self, path, **kwargs):
        self.calls.append((path, kwargs.get("json")))
        answer = self.responses[path]
        return answer(kwargs.get("json")) if callable(answer) else answer

    async def get(self, path):
        self.calls.append((path, None))
        return self.responses[path]


def fake(text=None, api=None, consent=True, contact=None):
    message = SimpleNamespace(text=text, reply_text=AsyncMock(), forward_origin=None, contact=contact)
    update = SimpleNamespace(effective_user=SimpleNamespace(id=1, first_name="Rosa"), effective_chat=SimpleNamespace(id=10),
                             effective_message=message, callback_query=None)
    context = SimpleNamespace(user_data={"consent": consent}, args=[], application=SimpleNamespace(bot_data={"api": api}),
                              bot=SimpleNamespace(send_message=AsyncMock(), send_chat_action=AsyncMock(), username="DesenmascaraBot"),
                              job_queue=MagicMock())
    return update, context


def replies(update) -> list[str]:
    return [call.args[0] for call in update.effective_message.reply_text.call_args_list]


def test_greeting_shows_the_menu():
    update, context = fake("Hola", FakeApi({}))
    asyncio.run(handlers.on_text(update, context))
    assert replies(update) == [textos.BIENVENIDA]


def test_asks_for_consent_first():
    api = FakeApi({"/bot/inicio": {"consentimiento": False}})
    update, context = fake("Mira este mensaje", api, consent=False)
    asyncio.run(handlers.on_text(update, context))
    assert replies(update) == [textos.CONSENTIMIENTO] and api.calls == [("/bot/inicio", {"telegram_id": 1, "chat_id": 10, "nombre": "Rosa"})]


def test_a_pasted_number_is_checked_in_the_banco():
    api = FakeApi({"/bot/numero": {"encontrado": False}})
    update, context = fake("310 000 0000", api)
    asyncio.run(handlers.on_text(update, context))
    assert api.calls[0][0] == "/bot/numero" and "SIN REPORTES" in replies(update)[0]
    assert context.user_data["reportables"] == [("telefono", "310 000 0000")]


def test_verified_call_asks_for_the_phone_then_retries():
    states = iter([{"estado": "falta_telefono", "entidad": "BancoAndino"},
                   {"estado": "real", "entidad": "BancoAndino", "motivo": "Confirmar una compra", "codigo": "4821"}])
    api = FakeApi({"/bot/llamada": lambda _: next(states), "/bot/telefono": {"ok": True}})
    update, context = fake("¿BancoAndino me está llamando?", api)
    asyncio.run(handlers.on_text(update, context))
    assert replies(update) == [textos.PEDIR_TELEFONO]

    update.effective_message.contact = SimpleNamespace(user_id=1, phone_number="573100000000")
    asyncio.run(handlers.on_contact(update, context))
    assert [path for path, _ in api.calls] == ["/bot/llamada", "/bot/telefono", "/bot/llamada"]
    assert "SÍ, ES REAL" in replies(update)[-1] and context.user_data["codigo_pendiente"] is True


def test_someone_elses_contact_is_rejected():
    api = FakeApi({})
    update, context = fake(api=api, contact=SimpleNamespace(user_id=999, phone_number="573100000000"))
    asyncio.run(handlers.on_contact(update, context))
    assert api.calls == [] and "propio número" in replies(update)[0]


def test_falso_familiar_asks_the_real_relative():
    analysis = {"resultado": result("medium", 55, modalidad="falso_familiar").model_dump(mode="json"),
                "preguntas_circulo": [{"aviso_id": "a1", "chat_id": 5010, "nombre": "Juan"}], "avisar_familiares": []}
    api = FakeApi({"/bot/analizar": analysis})
    update, context = fake("Hola ma, soy Juan, cambié de número. Mándame plata urgente", api)
    asyncio.run(handlers.on_text(update, context))
    assert "Dice ser" in replies(update)[0] and "Juan" in replies(update)[0]
    chat_id, question = context.bot.send_message.call_args.args
    assert chat_id == 5010 and "¿Fuiste tú?" in question
    context.job_queue.run_once.assert_called_once()


def test_relative_says_no_and_the_circle_is_alerted():
    api = FakeApi({"/bot/circulo/responder": {"protegido_chat_id": 10, "familiar": "Juan", "respuesta": "no", "otros_chat_ids": [77]}})
    update, context = fake(api=api)
    update.callback_query = SimpleNamespace(edit_message_reply_markup=AsyncMock())
    context.job_queue.get_jobs_by_name.return_value = []
    asyncio.run(handlers._answer_question(update, context, "resp:a1:no"))
    sent = {call.args[0]: call.args[1] for call in context.bot.send_message.call_args_list}
    assert "ES UNA ESTAFA" in sent[10] and "ALERTA DE TU CÍRCULO" in sent[77]


# --- Validating the relative who accepts a Círculo invitation -----------------------------------

def test_adding_a_relative_asks_for_their_number():
    api = FakeApi({"/bot/circulo/invitar": lambda body: {"token": "tok", "telefono": "+57 310 ••• 4567", "vence_en_horas": 48}})
    update, context = fake("Rosa", api)
    context.user_data["modo"] = "circulo_nombre"
    asyncio.run(handlers.on_text(update, context))
    assert "número de celular de *Rosa*" in replies(update)[0] and context.user_data["modo"] == "circulo_telefono"
    update.effective_message.text = "310 123 4567"
    asyncio.run(handlers.on_text(update, context))
    assert api.calls[-1] == ("/bot/circulo/invitar", {"telegram_id": 1, "chat_id": 10, "nombre": "Rosa", "familiar": "Rosa", "telefono": "310 123 4567"})
    message = replies(update)[-1]
    assert "start\\=c\\_tok" in message and "Vence en 48 horas" in message and "`+57 310 ••• 4567`" in message
    assert context.user_data["modo"] is None


def contact_update(api, phone="+57 310 123 4567"):
    update, context = fake(None, api, contact=SimpleNamespace(user_id=1, phone_number=phone))
    context.user_data["invitacion_token"] = "tok"
    return update, context


def test_the_relative_shares_their_number_and_the_protected_person_confirms():
    api = FakeApi({"/bot/circulo/aceptar": {"estado": "por_aprobar", "protegido_chat_id": 77, "protegido": "Mike", "familiar": "Rosa",
                                            "miembro_id": "m1", "telefono": "+57 310 ••• 4567"}})
    update, context = contact_update(api)
    asyncio.run(handlers.on_contact(update, context))
    assert api.calls == [("/bot/circulo/aceptar", {"telegram_id": 1, "chat_id": 10, "nombre": "Rosa", "token": "tok", "acepta": True,
                                                   "telefono": "+57 310 123 4567"})]
    assert "tu número coincide" in replies(update)[0]
    sent = context.bot.send_message.call_args
    assert sent.args[0] == 77 and "VALIDAR FAMILIAR" in sent.args[1] and "`+57 310 ••• 4567`" in sent.args[1]
    buttons = [b.callback_data for b in sent.kwargs["reply_markup"].inline_keyboard[0]]
    assert buttons == ["apr:m1:1", "apr:m1:0"]


def test_another_number_is_turned_away_and_the_protected_person_warned():
    api = FakeApi({"/bot/circulo/aceptar": {"estado": "no_coincide", "protegido_chat_id": 77, "protegido": "Mike", "familiar": "Rosa",
                                            "miembro_id": "m1", "telefono": "+57 300 ••• 0000"}})
    update, context = contact_update(api, "+57 300 999 0000")
    asyncio.run(handlers.on_contact(update, context))
    assert "EL NÚMERO NO COINCIDE" in replies(update)[0]
    warning = context.bot.send_message.call_args.args
    assert warning[0] == 77 and "INTENTO DE ENTRAR" in warning[1] and "`+57 300 ••• 0000`" in warning[1]


def test_the_protected_person_approves():
    api = FakeApi({"/bot/circulo/aprobar": {"familiar": "Rosa", "familiar_chat_id": 55, "aprueba": True}})
    update, context = fake(None, api)
    update.callback_query = SimpleNamespace(data="apr:m1:1", answer=AsyncMock(), edit_message_reply_markup=AsyncMock())
    asyncio.run(handlers.on_button(update, context))
    assert api.calls[-1] == ("/bot/circulo/aprobar", {"telegram_id": 1, "chat_id": 10, "nombre": "Rosa", "miembro_id": "m1", "aprueba": True})
    assert "ya está en tu Círculo de Confianza, validado" in replies(update)[0]
    assert context.bot.send_message.call_args.args[0] == 55


def test_accepting_asks_for_the_number_first():
    api = FakeApi({})
    update, context = fake(None, api)
    update.callback_query = SimpleNamespace(data="acc:tok:1", answer=AsyncMock(), edit_message_reply_markup=AsyncMock())
    asyncio.run(handlers.on_button(update, context))
    assert api.calls == [] and context.user_data["invitacion_token"] == "tok"
    keyboard = update.effective_message.reply_text.call_args.kwargs["reply_markup"].keyboard[0][0]
    assert keyboard.text == "Compartir mi número" and keyboard.request_contact


# --- ¿Me están llamando de verdad?: buttons and a pasted code ------------------------------------

def test_option_2_offers_the_connected_entities_as_buttons():
    api = FakeApi({"/bot/entidades": {"entidades": ["Desenmascara"]}})
    update, context = fake(None, api)
    update.callback_query = SimpleNamespace(data="m2", answer=AsyncMock(), edit_message_reply_markup=AsyncMock())
    asyncio.run(handlers.on_button(update, context))
    button = update.effective_message.reply_text.call_args.kwargs["reply_markup"].inline_keyboard[0][0]
    assert button.text == "📞 Desenmascara" and button.callback_data == "ent:Desenmascara"


def test_tapping_an_entity_asks_about_it():
    api = FakeApi({"/bot/llamada": {"estado": "real", "entidad": "Desenmascara", "motivo": "Confirmar una compra", "codigo": "0346"}})
    update, context = fake(None, api)
    update.callback_query = SimpleNamespace(data="ent:Desenmascara", answer=AsyncMock(), edit_message_reply_markup=AsyncMock())
    asyncio.run(handlers.on_button(update, context))
    assert api.calls[-1][1]["texto"] == "Desenmascara" and "SÍ, ES REAL" in replies(update)[0]


def test_a_code_pasted_from_the_panel_is_read_as_a_code():
    api = FakeApi({"/bot/llamada/confirmar": {"estado": "correcto", "entidad": "Desenmascara"}})
    update, context = fake("0\n3\n4\n6", api)
    context.user_data["modo"] = "llamada"
    asyncio.run(handlers.on_text(update, context))
    assert api.calls == [("/bot/llamada/confirmar", {"telegram_id": 1, "chat_id": 10, "nombre": "Rosa", "codigo": "0346"})]
    assert "CÓDIGO CORRECTO" in replies(update)[0]


def test_a_code_without_a_shared_number_asks_for_it_then_checks():
    answers = iter([{"estado": "falta_telefono"}, {"estado": "correcto", "entidad": "Desenmascara"}])
    api = FakeApi({"/bot/llamada/confirmar": lambda _: next(answers), "/bot/telefono": {"ok": True}})
    update, context = fake("0346", api, contact=SimpleNamespace(user_id=1, phone_number="+57 313 389 8638"))
    context.user_data["modo"] = "llamada"
    asyncio.run(handlers.on_text(update, context))
    assert replies(update) == [textos.PEDIR_TELEFONO]
    asyncio.run(handlers.on_contact(update, context))
    assert "CÓDIGO CORRECTO" in replies(update)[-1]


# --- «Me está llamando este número, ¿contesto?» -------------------------------------------------

def test_the_first_line_says_whether_to_answer():
    reported = {"encontrado": True, "valor": "+57 300 ••• 0209", "personas": 5, "reportes": 7, "modalidad": "Falso asesor del banco",
                "estado": "normal", "oficial_de": None}
    assert format_number(reported | {"nivel": 85}).startswith("🔴 *NO CONTESTES · \+57 300 ••• 0209*")
    assert format_number(reported | {"nivel": 40}).startswith("🟡 *CUIDADO · \+57 300 ••• 0209*")
    unknown = format_number({"encontrado": False, "puede_verificar": False})
    assert unknown.startswith("🟡 *CONTESTA CON CUIDADO · SIN REPORTES*") and "opción 2" in unknown


def test_a_call_an_entity_registered_says_answer_and_ask_for_the_code():
    info = {"encontrado": False, "puede_verificar": True,
            "llamada_registrada": {"entidad": "Desenmascara", "motivo": "Confirmar una compra", "asesor": "Laura M.", "codigo": "0346",
                                   "hace_min": 2, "es_su_linea": False}}
    message = format_number(info)
    assert message.startswith("🟢 *CONTESTA Y PIDE EL CÓDIGO*") and "hace 2 minutos" in message and "`0 3 4 6`" in message
    assert_valid_markdown(message)
