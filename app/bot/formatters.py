"""Telegram MarkdownV2 messages. Every dynamic or fixed text goes through esc(): one unescaped
'.' makes Telegram reject the whole message.

Rules from the guide (section 8): the semáforo with its word on the first line, at most
8-10 lines, simple words, always say what to do, never claim 100 %.
"""

import re
from typing import Any

from app.engine.pistas import plural
from app.schemas.contract import AnalysisResult

MARKDOWN_V2_SPECIALS = re.compile(r"([_\*\[\]()~`>#+\-=|{}.!\\])")
SEMAFORO = {
    "high": ("🔴", "ALTO RIESGO"),
    "medium": ("🟡", "SOSPECHOSO"),
    "low": ("🟢", "BAJO RIESGO"),
    "inconclusive": ("⚪", "NO CONCLUYENTE"),
}
MAX_SIGNALS = 3


def esc(value: Any) -> str:
    return MARKDOWN_V2_SPECIALS.sub(r"\\\1", str(value))


def b(value: Any) -> str:
    return f"*{esc(value)}*"


def it(value: Any) -> str:
    return f"_{esc(value)}_"


def code(value: Any) -> str:
    """Inline code: Telegram draws it in a box and copies it with one tap. Inside, only ` and \\ are special."""
    return "`" + str(value).replace("\\", "\\\\").replace("`", "\\`") + "`"


def join(*lines: str) -> str:
    message = "\n".join(line for line in lines if line is not None)
    # Telegram limits messages to 4096 characters. Leave room for the truncation notice.
    if len(message) > 3900:
        message = message[:3850].rsplit("\n", 1)[0] + "\n\n_Resultado abreviado por límite de longitud\\._"
    return message


def header(level: str, score: int | None = None, category: str | None = None) -> str:
    dot, word = SEMAFORO[level]
    title = word if score is None or level == "inconclusive" else f"{word} · {score}/100"
    return f"{dot} {b(title)}" + (f" · {esc(category)}" if category else "")


def format_analysis(result: AnalysisResult) -> str:
    level = result.risk_level.value
    category = result.category or (result.summary if level in ("low", "inconclusive") else None)
    lines = [header(level, result.risk_score, category)]
    reasons = [s for s in result.signals if s.points > 0][:MAX_SIGNALS]
    if level == "low":
        reasons = [s for s in result.signals if s.points <= 0][:1]
    if reasons:
        lines.append(b("Por qué:"))
        lines.extend(f"• {esc(s.label)}" for s in reasons)
    elif level == "inconclusive":
        lines.append(esc("No pude completar el análisis en este momento."))
    todo = result.recommendations[0] if result.recommendations else "Verifica por otro canal antes de compartir datos o realizar pagos."
    lines.append(f"{b('Qué hacer:')} {esc(todo)}")
    if len(result.recommendations) > 1:
        lines.append(esc(result.recommendations[-1]))
    return join(*lines)


def format_heard(text: str) -> str:
    snippet = text if len(text) <= 160 else text[:157] + "…"
    return f"{it('Entendí:')} «{esc(snippet)}»"


def format_call(info: dict) -> str:
    entidad = info.get("entidad", "")
    if info["estado"] == "real":
        return join(
            f"🟢 {b('SÍ, ES REAL')}",
            f"{b(entidad)} {esc('te está llamando.')}",
            f"{esc('Motivo:')} {b(info['motivo'])}{esc('.')}",
            esc("Pídele a quien te llama que te diga este código:"),
            code(" ".join(info["codigo"])),
            f"{esc('Si no lo sabe,')} {b('cuelga')}{esc('.')}",
        )
    lineas = info.get("lineas_oficiales") or []
    return join(
        f"🔴 {b('NO ES TU BANCO')}",
        f"{b(entidad)} {b('no tiene ninguna llamada registrada')} {esc('hacia tu número en este momento.')}",
        f"{b('Qué hacer: cuelga ya.')} {esc('Si necesitas hablar con la entidad, llama tú a la línea de tu tarjeta' + (f' ({lineas[0]})' if lineas else '') + '.')}",
        esc("¿Quieres reportar el número que te llamó? Envíamelo."),
    )


def format_not_connected(info: dict) -> str:
    """A real entity that has not joined Llamada Verificada: we cannot know, so we never say it is false."""
    entidad = info["entidad"]
    donde = f"en tu tarjeta o en {info['sitio']}" if info.get("sitio") else "en tu tarjeta"
    if info.get("linea"):
        donde = f"en tu tarjeta o a su línea oficial {info['linea']}"
    return join(
        f"🟡 {b('NO PUEDO CONFIRMARLO')}",
        f"{b(entidad)} {esc('todavía no está conectada a Llamada Verificada, así que no sé si de verdad es ella.')}",
        f"{b('Qué hacer:')} {esc(f'cuelga y llama tú a la línea que aparece {donde}.')}",
        esc("Nunca dictes claves ni códigos por teléfono, aunque digan ser del banco."),
        esc("¿Te llamaron de un número que no conoces? Envíamelo y lo reviso en el Banco de números."),
    )


def format_code(info: dict) -> str:
    if info["estado"] == "correcto":
        return join(
            f"🟢 {b('CÓDIGO CORRECTO')}",
            f"{esc('Es')} {b(info['entidad'])} {esc('de verdad. Puedes seguir la llamada.')}",
            f"{esc('Aun así,')} {b('nunca dictes claves')} {esc('ni códigos que te lleguen por mensaje.')}",
        )
    return join(
        f"🔴 {b('EL CÓDIGO NO COINCIDE')}",
        f"{b('Cuelga ya.')} {esc('Llama tú a la línea oficial que está en tu tarjeta.')}",
    )


def format_number(info: dict) -> str:
    valor = info.get("valor") or "Este número"
    if info.get("sitio"):  # a line the entity publishes: it confirms where to call, never a call
        return join(
            f"🟢 {b('LÍNEA OFICIAL')}",
            f"{esc('Es una línea de')} {b(info['oficial_de'])}{esc(', publicada en su página ' + info['sitio'] + '.')}",
            f"{esc('Si te')} {b('llamaron')} {esc('desde este número, no basta: se puede falsificar en pantalla.')}",
            f"{b('Qué hacer:')} {esc('cuelga y llama tú a este mismo número para confirmar.')}",
        )
    if info.get("oficial_de"):
        return join(
            f"🟢 {b('NÚMERO OFICIAL')}",
            f"{esc('Es un número que')} {b(info['oficial_de'])} {esc('registró en Desenmascara.')}",
            f"{esc('Si te')} {b('escribe')} {esc('desde este número, es la entidad.')}",
            f"{esc('Si te')} {b('llamó')} {esc('con este número, no basta: se puede falsificar. Usa la opción 2.')}",
        )
    if info.get("estado") == "en_revision":
        return join(
            f"🟡 {b('EN REVISIÓN')}",
            esc("Este número tiene reportes, pero su dueño pidió revisión. Mientras tanto, no podemos decir que sea una estafa."),
            f"{b('Qué hacer:')} {esc('si dice ser tu banco, cuelga y llama tú a la línea oficial.')}",
        )
    if not info.get("encontrado") or info.get("personas", 0) == 0:
        return join(
            f"⚪ {b('SIN REPORTES')}",
            esc("Nadie ha reportado este número todavía. Eso no garantiza que sea seguro."),
            f"{b('Ojo:')} {esc('el número que ves en pantalla se puede falsificar.')}",
            f"{b('Qué hacer:')} {esc('si dice ser tu banco, cuelga y llama tú a la línea oficial de tu tarjeta.')}",
            esc("¿Te pidieron un código o datos? Cuéntame la llamada en una nota de voz."),
        )
    level = "high" if info["nivel"] >= 70 else ("medium" if info["nivel"] >= 40 else "low")
    dot, word = SEMAFORO[level]
    reportes = plural(info["reportes"], "reporte", "reportes")
    personas = plural(info["personas"], "persona", "personas")
    modalidad = f" como «{info['modalidad'].lower()}»" if info.get("modalidad") else ""
    return join(
        f"{dot} {b(word + ' · ' + valor)}",
        f"{b(reportes)} {esc(f'de {personas}{modalidad}.')}",
        f"{b('Ojo:')} {esc('el número que ves en pantalla se puede falsificar.')}",
        f"{b('Qué hacer:')} {esc('cuelga y llama tú a la línea oficial de tu tarjeta.')}",
        esc("¿Te pidieron un código? Cuéntame la llamada en una nota de voz."),
    )


def format_report(info: dict) -> str:
    if not info["nuevo"]:
        return esc("Ya tenías un reporte de este número: cada persona cuenta una sola vez. Gracias por proteger a otros.")
    personas = info["personas"]
    return join(
        b("Reportado"),
        f"{esc(info['valor'])} {esc('ya tiene')} {b(plural(personas, 'persona', 'personas'))} "
        f"{esc('que lo reportó.' if personas == 1 else 'que lo reportaron.')}",
        esc("Si alguien más pregunta por él, le avisaremos. Gracias por proteger a otros."),
    )
