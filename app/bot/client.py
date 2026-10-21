"""Telegram entry point. All risk evaluation is delegated to the FastAPI API.

    python -m app.bot.client
"""

import logging

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.bot import handlers
from app.bot.api import Api
from app.core.config import settings

COMMANDS = [
    BotCommand("start", "Empezar y ver el menú"),
    BotCommand("menu", "Las 6 opciones"),
    BotCommand("circulo", "Mi Círculo de Confianza"),
    BotCommand("kit", "Kit de denuncia de lo último que revisé"),
    BotCommand("revision", "Mi número aparece reportado por error"),
    BotCommand("ayuda", "Cómo usarme"),
    BotCommand("borrar", "Borrar mis datos"),
]


async def _post_init(application: Application) -> None:
    application.bot_data["api"] = Api()
    await application.bot.set_my_commands(COMMANDS)


async def _post_shutdown(application: Application) -> None:
    await application.bot_data["api"].close()


def create_application(token: str) -> Application:
    application = ApplicationBuilder().token(token).post_init(_post_init).post_shutdown(_post_shutdown).build()
    private = filters.ChatType.PRIVATE
    application.add_handler(CommandHandler("start", handlers.start_command, filters=private))
    application.add_handler(CommandHandler(["menu", "inicio"], handlers.menu_command, filters=private))
    application.add_handler(CommandHandler(["help", "ayuda"], handlers.help_command, filters=private))
    application.add_handler(CommandHandler("circulo", handlers.circle_command, filters=private))
    application.add_handler(CommandHandler(["kit", "denunciar"], handlers.kit_command, filters=private))
    application.add_handler(CommandHandler("revision", handlers.review_command, filters=private))
    application.add_handler(CommandHandler("borrar", handlers.forget_command, filters=private))
    application.add_handler(CallbackQueryHandler(handlers.on_button))
    application.add_handler(MessageHandler(private & filters.CONTACT, handlers.on_contact))
    application.add_handler(MessageHandler(private & (filters.PHOTO | filters.Document.IMAGE), handlers.on_photo))
    application.add_handler(MessageHandler(private & (filters.VOICE | filters.AUDIO), handlers.on_voice))
    application.add_handler(MessageHandler(private & filters.TEXT & ~filters.COMMAND, handlers.on_text))
    application.add_handler(MessageHandler(private & ~filters.COMMAND, handlers.on_unsupported))
    application.add_error_handler(handlers.on_error)
    return application


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # its INFO lines would print the bot token in URLs
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise SystemExit("Configura TELEGRAM_BOT_TOKEN en el archivo .env o en el entorno para iniciar el bot.")
    if not settings.BOT_API_SECRET:
        raise SystemExit("Falta BOT_API_SECRET. Ejecuta `python scripts/setup_local.py`.")
    create_application(token).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
