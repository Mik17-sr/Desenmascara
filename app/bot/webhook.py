"""The bot inside the API, by webhook: Telegram sends each update to POST /telegram/webhook.

On Render's free plan there is no process for polling (a worker is paid), and a web service that sleeps after
15 minutes wakes up with Telegram's next request. The bot still talks to the API over HTTP (API_BASE_URL), as on
your computer: the same code answers in both places.
"""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request
from telegram import Update
from telegram.ext import Application

from app.bot import client
from app.core.config import settings

logger = logging.getLogger(__name__)
PATH = "/telegram/webhook"
router = APIRouter()


def secret() -> str:
    """Telegram repeats it in X-Telegram-Bot-Api-Secret-Token, so nobody else can send the bot fake messages."""
    return hmac.new(settings.BOT_API_SECRET.encode(), b"telegram-webhook", hashlib.sha256).hexdigest()


def public_url() -> str | None:
    base = settings.TELEGRAM_WEBHOOK_URL or settings.RENDER_EXTERNAL_URL
    return base.rstrip("/") + PATH if base and settings.TELEGRAM_BOT_TOKEN and settings.BOT_API_SECRET else None


async def start() -> Application | None:
    """None on your computer (no public address): there the bot runs by polling, with python -m app.bot.client."""
    url = public_url()
    if url is None:
        return None
    logging.getLogger("httpx").setLevel(logging.WARNING)  # its INFO lines would print the bot token in URLs
    application = client.create_application(settings.TELEGRAM_BOT_TOKEN, polling=False)
    await application.initialize()
    await client.post_init(application)
    await application.start()
    await application.bot.set_webhook(url, secret_token=secret(), allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram webhook at %s", url)
    return application


async def stop(application: Application) -> None:
    await application.stop()
    await client.post_shutdown(application)
    await application.shutdown()


@router.post(PATH, include_in_schema=False)
async def receive(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)) -> dict:
    application: Application | None = request.app.state.telegram
    if application is None or not hmac.compare_digest(x_telegram_bot_api_secret_token or "", secret()):
        raise HTTPException(status_code=401, detail="No autorizado.")
    # Answer Telegram at once; the handlers run from the queue, several at a time (a screenshot takes a while).
    await application.update_queue.put(Update.de_json(await request.json(), application.bot))
    return {"ok": True}
