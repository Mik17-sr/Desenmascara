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
    assert message.startswith("🟢 *LÍNEA OFICIAL*") and "se puede falsificar" in message and "bancolombia\\.com" in message
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
