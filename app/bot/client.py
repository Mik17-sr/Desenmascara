"""Telegram entry point. All risk evaluation is delegated to the FastAPI API.

    python -m app.bot.client
"""

import logging
from pathlib import Path

from telegram import Bot, BotCommand, InputProfilePhotoStatic, Update
from telegram.error import TelegramError
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

# The bot's profile, as in the guide: the platform's name, "bot antiestafas" and the mask logo.
AVATAR = Path(__file__).parent / "assets" / "avatar.png"
NOMBRE = "Desenmascara"
DESCRIPCION_CORTA = "Bot antiestafas: reenvía el mensaje, la captura, el número o la nota de voz y te digo si es una estafa."
DESCRIPCION = (
    "Reenvía el mensaje. Desenmascara la estafa.\n\n"
    "Envíame un mensaje, una captura, el número que te llamó o una nota de voz y en segundos te doy un semáforo "
    "(🟢 bajo riesgo, 🟡 sospechoso o 🔴 alto riesgo), el porqué y qué hacer.\n\n"
    "Cuando puedo, confirmo con la fuente: tu banco con Llamada Verificada o tu familiar con el Círculo de Confianza.\n\n"
    "Solo leo lo que tú me envíes."
)

logger = logging.getLogger(__name__)


async def _profile(bot: Bot) -> None:
    """Send only what differs: Telegram rate-limits these calls. The logo goes up once, when there is no photo."""
    if (await bot.get_my_name()).name != NOMBRE:
        await bot.set_my_name(NOMBRE)
    if (await bot.get_my_short_description()).short_description != DESCRIPCION_CORTA:
        await bot.set_my_short_description(DESCRIPCION_CORTA)
    if (await bot.get_my_description()).description != DESCRIPCION:
        await bot.set_my_description(DESCRIPCION)
    if not (await bot.get_user_profile_photos(bot.id, limit=1)).total_count:
        await bot.set_my_profile_photo(InputProfilePhotoStatic(AVATAR.read_bytes()))


async def _post_init(application: Application) -> None:
    application.bot_data["api"] = Api()
    await application.bot.set_my_commands(COMMANDS)
    try:
        await _profile(application.bot)
    except TelegramError as exc:  # a rate limit must not stop the bot
        logger.warning("Could not update the bot profile: %r", exc)


async def _post_shutdown(application: Application) -> None:
    await application.bot_data["api"].close()


def create_application(token: str) -> Application:
    # A screenshot takes 10-16 s: one at a time, a button tapped meanwhile waits in line until Telegram expires it.
    application = (ApplicationBuilder().token(token).post_init(_post_init).post_shutdown(_post_shutdown)
                   .concurrent_updates(True).build())
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
