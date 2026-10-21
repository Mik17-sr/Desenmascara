"""Telegram entry point. All risk evaluation is delegated to the FastAPI API."""

import os
import re
from typing import Any
from urllib.parse import urlsplit

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.schemas.contract import AnalysisInput, AnalysisResult, RiskLevel


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
ANALYZE_URL = f"{API_BASE_URL}/api/v1/analyze"
ANALYSIS_TIMEOUT_SECONDS = 8.0
MAX_INPUT_LENGTH = 4000
URL_PATTERN = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
MARKDOWN_V2_SPECIALS = re.compile(r"([_\*\[\]()~`>#+\-=|{}.!\\])")

RISK_LABELS = {
    RiskLevel.LOW: "Bajo",
    RiskLevel.MEDIUM: "Medio",
    RiskLevel.HIGH: "Alto",
    RiskLevel.INCONCLUSIVE: "No concluyente",
}


def extract_urls(text: str) -> list[str]:
    """Extract URL-shaped strings without opening or resolving them."""
    urls = []
    for match in URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(".,!?;:")
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        if url.startswith("www."):
            url = f"https://{url}"
        try:
            parsed = urlsplit(url)
        except ValueError:
            continue
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            urls.append(url)
    return list(dict.fromkeys(urls))


def _escape(value: Any) -> str:
    return MARKDOWN_V2_SPECIALS.sub(r"\\\1", str(value))


def format_analysis(result: AnalysisResult) -> str:
    risk_label = RISK_LABELS[result.risk_level]
    lines = [
        "*Evaluación de Riesgo*",
        f"Nivel: *{_escape(risk_label)}* · Puntaje heurístico: *{result.risk_score}/100*",
        "",
        "*Qué observamos*",
    ]
    if result.signals:
        for signal in result.signals:
            lines.append(f"• *{_escape(signal.label)}*: {_escape(signal.evidence)}")
    else:
        lines.append(_escape(result.summary))

    if result.links:
        for link in result.links:
            lines.append(f"• Enlace {_escape(link.status.value)}: {_escape(link.reason)}")

    lines.extend(["", "*Qué hacer*"])
    if result.recommendations:
        lines.extend(f"• {_escape(item)}" for item in result.recommendations)
    else:
        lines.append("• Verifica por otro canal antes de compartir datos o realizar pagos.")

    lines.extend(["", "*Limitaciones*"])
    if result.limitations:
        lines.extend(f"• {_escape(item)}" for item in result.limitations)
    else:
        lines.append("• El análisis automático puede equivocarse; revisa el contexto por tu cuenta.")

    # Telegram limits messages to 4096 characters. Leave room for the truncation notice.
    message = "\n".join(lines)
    if len(message) > 3900:
        message = message[:3850].rsplit("\n", 1)[0] + "\n\n_Resultado abreviado por límite de longitud\._"
    return message


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "Soy Desenmascara. Envíame un mensaje o enlace sospechoso y pediré su análisis al servicio.\n\n"
            "El análisis automático tiene límites: un riesgo bajo no garantiza que algo sea legítimo. "
            "No compartas contraseñas, códigos de verificación ni datos bancarios."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "Envía el texto sospechoso o un enlace para analizarlo. No abras enlaces por precaución "
            "y elimina del mensaje cualquier dato personal que no sea necesario."
        )


async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    text = (message.text or "").strip()
    if not text:
        await message.reply_text("Envía un mensaje de texto o un enlace para analizarlo.")
        return
    if len(text) > MAX_INPUT_LENGTH:
        await message.reply_text("El texto supera el máximo de 4000 caracteres. Envíame una versión más corta.")
        return

    payload = AnalysisInput(text=text, source="telegram", links=extract_urls(text))
    try:
        async with httpx.AsyncClient(timeout=ANALYSIS_TIMEOUT_SECONDS) as client:
            response = await client.post(ANALYZE_URL, json=payload.model_dump(mode="json"))
            response.raise_for_status()
            result = AnalysisResult.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        await message.reply_text(
            "No pude obtener el análisis en este momento. Inténtalo de nuevo más tarde."
        )
        return

    await message.reply_text(format_analysis(result), parse_mode=ParseMode.MARKDOWN_V2)


def create_application(token: str) -> Application:
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler(["help", "ayuda"], help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_message))
    return application


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Configura TELEGRAM_BOT_TOKEN en el entorno para iniciar el bot.")
    create_application(token).run_polling()


if __name__ == "__main__":
    main()
