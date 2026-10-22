"""Telegram MarkdownV2 messages. Every dynamic or fixed text goes through esc(): one unescaped
'.' makes Telegram reject the whole message.

Rules from the guide (section 8): the semáforo with its word on the first line, at most
8-10 lines, simple words, always say what to do, never claim 100 %.
"""

import re
from typing import Any

from app.core.security import normalize_phone
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
    reasons = list({s.label: s for s in result.signals if s.points > 0}.values())[:MAX_SIGNALS]
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


def format_report(reports: list[dict]) -> str:
    """The answer to «Reportar»: what went into the Banco and how many people back it, never the full number."""
    if not any(r["nuevo"] for r in reports):
        return join(
            f"✅ {b('YA LO HABÍAS REPORTADO')}",
            esc("Cada persona cuenta una sola vez. Gracias por proteger a otros."),
        )
    lines = [f"✅ {b('REPORTE RECIBIDO')}", esc("Gracias. Quedó registrado en el Banco de números de Desenmascara:")]
    for r in reports:
        count = plural(r["personas"], "persona lo reportó", "personas lo reportaron") if r["nuevo"] else "ya lo habías reportado"
        lines.append(f"• {code(r['valor'])} · {esc(count)}")
    one = len(reports) == 1
    lines.append(esc(f"Si alguien más pregunta por {'este dato' if one else 'estos datos'}, le avisaremos que "
                     f"{'tiene' if one else 'tienen'} reportes."))
    return join(*lines)


TIPO_DATO = {"telefono": "Teléfono", "llave": "Llave Bre-B", "cuenta": "Cuenta"}
FUENTE = {"texto": "mensaje de texto", "captura": "captura de pantalla", "voz": "nota de voz"}


def pretty_phone(value: str) -> str:
    """'573044722062' -> '+57 304 472 2062': the kit is for the police, so it shows the number whole."""
    digits = normalize_phone(value) or ""
    return f"+57 {digits[2:5]} {digits[5:8]} {digits[8:]}" if digits.startswith("57") and len(digits) == 12 else value


def _listing(items: list[str], last: str = " y ") -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + last + items[-1]


RELATO_DATO = {"telefono": ("el teléfono", "los teléfonos"), "llave": ("la llave Bre-B", "las llaves Bre-B"),
               "cuenta": ("la cuenta", "las cuentas"), "enlace": ("el enlace", "los enlaces")}


def relato(kit: dict) -> str:
    """The account of the facts for the police form, in first person. Built only from what was analysed: it never
    invents an amount, a date or a number, so what the person lost is left for them to add."""
    fuente = kit.get("fuente", "texto")
    como = f", que identificó como «{kit['categoria']}»" if kit.get("categoria") else ""
    cuando = f"El {kit['dia']}, a las {kit['hora']}," if kit.get("dia") else "Hoy"
    snippet = " ".join((kit.get("texto") or "").split())
    snippet = snippet if len(snippet) <= 400 else snippet[:397] + "…"
    if fuente == "voz":
        parts = [f"{cuando} conté en Desenmascara una llamada que recibí{como}."]
        if snippet:
            parts.append(f"Lo que me dijeron: «{snippet}».")
    else:
        parts = [f"{cuando} revisé en Desenmascara un mensaje que recibí{como}."]
        if fuente == "captura":
            parts.append("Anexo la captura de pantalla.")
        elif snippet:
            parts.append(f"El mensaje dice: «{snippet}».")
    groups = {}
    for tipo, valor in kit.get("datos", []):
        if tipo in TIPO_DATO:
            groups.setdefault(tipo, []).append(pretty_phone(valor) if tipo == "telefono" else valor)
    if kit.get("enlaces"):
        groups["enlace"] = list(kit["enlaces"])
    if groups:
        donde = "En la llamada mencionaron" if fuente == "voz" else "En el mensaje aparecen"
        named = [f"{RELATO_DATO[t][len(v) > 1]} {_listing(v)}" for t, v in groups.items()]
        # "los teléfonos A y B, y el enlace C": the comma keeps the last group apart from a list that already has a "y".
        parts.append(f"{donde} " + _listing(named, ", y " if any(len(v) > 1 for v in groups.values()) else " y ") + ".")
    word = SEMAFORO[kit["nivel"]][1].lower()
    motivos = [m[0].lower() + m[1:].rstrip(".") for m in kit.get("motivos", []) if m]
    parts.append(f"Desenmascara lo calificó como {word} ({kit['puntaje']}/100)"
                 + (f" por estas señales: {'; '.join(motivos)}." if motivos else "."))
    return " ".join(parts)


def block(value: str) -> str:
    """A pre block: Telegram shows it with a «Copiar» button. Inside, only ` and \\ are special."""
    return "```\n" + value.replace("\\", "\\\\").replace("`", "\\`") + "\n```"


def format_kit(kit: dict, lineas: list[str]) -> str:
    """A summary to hand to the bank or the police. Links go in a box so that nobody opens them by mistake."""
    dot, word = SEMAFORO[kit["nivel"]]
    resultado = f"{word} · {kit['puntaje']}/100"
    fuente = kit.get("fuente", "texto")
    datos = [(tipo, valor) for tipo, valor in kit.get("datos", []) if tipo in TIPO_DATO]
    lines = [
        f"📋 {b('KIT DE DENUNCIA')}",
        it(f"Desenmascara · Referencia {kit['referencia']}") if kit.get("referencia") else None,
        "",
        f"{b('Fecha:')} {esc(kit['dia'] + ', ' + kit['hora'] + ' (hora de Colombia)')}",
        f"{b('Resultado:')} {dot} {esc(resultado)}",
        f"{b('Modalidad:')} {esc(kit['categoria'])}" if kit.get("categoria") else None,
        f"{b('Evidencia:')} {esc(FUENTE[fuente])}",
        f"{b('Reporte:')} {esc('registrado en el Banco de números de Desenmascara.')}" if kit.get("reportado") else None,
    ]
    if datos or kit.get("enlaces"):
        lines += ["", b("Datos que aparecen en el mensaje")]
        lines += [f"• {esc(TIPO_DATO[tipo])}: {code(pretty_phone(valor) if tipo == 'telefono' else valor)}" for tipo, valor in datos]
        lines += [f"• {esc('Enlace')}: {code(url)}" for url in kit.get("enlaces", [])]
    lines += ["", f"{b('Relato de los hechos')} {it('(cópialo en tu denuncia)')}", block(relato(kit)),
              f"{b('Completa:')} {esc('si entregaste dinero o datos, agrega cuánto, cuándo y por qué medio.')}"]
    lines += ["", b("Dónde denunciar"), *[esc(f"{n}. {line}") for n, line in enumerate(lineas, 1)]]
    consejo = "no borres el chat y no respondas más a ese número."
    if fuente == "captura":
        consejo = "adjunta la captura original a la denuncia, " + consejo
    lines += ["", f"{b('Consejo:')} {esc(consejo)}"]
    return join(*lines)
