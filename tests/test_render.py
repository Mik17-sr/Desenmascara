"""Publishing on Render (render.yaml): the bot by webhook inside the API, and the rules alone without Ollama."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from app.bot import webhook
from app.core.config import settings
from tests.conftest import fake_ai

BLUEPRINT = Path(__file__).resolve().parent.parent / "render.yaml"
SECRETS = {"DATABASE_URL", "TELEGRAM_BOT_TOKEN", "HMAC_SECRET", "ENCRYPTION_KEY", "BOT_API_SECRET", "ADMIN_API_KEY"}
UPDATE = {"update_id": 1, "message": {"message_id": 1, "date": 0, "text": "Hola",
                                      "chat": {"id": 10, "type": "private"}, "from": {"id": 1, "is_bot": False, "first_name": "Rosa"}}}


def test_the_blueprint_never_holds_a_secret():
    services = {s["name"]: s for s in yaml.safe_load(BLUEPRINT.read_text(encoding="utf-8"))["services"]}
    api = {v["key"]: v for v in services["desenmascara-api"]["envVars"]}
    assert all(api[key].get("sync") is False and "value" not in api[key] for key in SECRETS)
    # The bot inside the service calls the API at its own port; no Ollama there.
    assert api["API_BASE_URL"]["value"].endswith(":" + str(api["PORT"]["value"])) and api["IA_LOCAL"]["value"] == "false"
    # The Dashboard as a static site: Next exports out/ only with NEXT_OUTPUT=export (dashboard/next.config.ts).
    dashboard = services["desenmascara-dashboard"]
    assert dashboard["runtime"] == "static" and dashboard["rootDir"] == "dashboard" and dashboard["staticPublishPath"] == "out"
    assert {"key": "NEXT_OUTPUT", "value": "export"} in dashboard["envVars"]
    assert 'process.env.NEXT_OUTPUT === "export"' in (BLUEPRINT.parent / "dashboard" / "next.config.ts").read_text(encoding="utf-8")


def test_on_a_computer_the_bot_stays_by_polling():
    assert webhook.public_url() is None  # no RENDER_EXTERNAL_URL in the tests


def test_render_gives_the_webhook_its_address(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", "https://desenmascara-api.onrender.com/")
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "123:abc")
    assert webhook.public_url() == "https://desenmascara-api.onrender.com/telegram/webhook"


def test_only_telegram_can_send_the_bot_updates(client):
    queue = SimpleNamespace(put=AsyncMock())
    client.app.state.telegram = SimpleNamespace(update_queue=queue, bot=None)
    try:
        assert client.post(webhook.PATH, json=UPDATE).status_code == 401
        assert client.post(webhook.PATH, json=UPDATE, headers={"X-Telegram-Bot-Api-Secret-Token": "otro"}).status_code == 401
        queue.put.assert_not_called()
        ok = client.post(webhook.PATH, json=UPDATE, headers={"X-Telegram-Bot-Api-Secret-Token": webhook.secret()})
        assert ok.status_code == 200
        update = queue.put.call_args.args[0]
        assert update.update_id == 1 and update.message.text == "Hola"
    finally:
        client.app.state.telegram = None


def test_without_ollama_the_rules_answer_alone(client, monkeypatch):
    monkeypatch.setattr(settings, "IA_LOCAL", False)
    with fake_ai() as classify:
        plain = client.post("/api/v1/analyze", json={"text": "¿Vamos al partido el sábado?", "source": "evaluacion"}).json()
        scam = client.post("/api/v1/analyze", json={"text": "Vendo moto en remate. Para apartarla consigna un anticipo hoy.",
                                                     "source": "evaluacion", "tipo": "compra"}).json()
    classify.assert_not_called()
    # Not "no concluyente" for every quiet message, as when the AI is merely slow.
    assert plain["risk_level"] == "low" and scam["risk_level"] == "high"
    assert client.get("/health").json()["ia"] == "apagada"


def test_the_bot_starts_by_webhook_when_published(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", "https://desenmascara-api.onrender.com")
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "123:abc")
    application = SimpleNamespace(initialize=AsyncMock(), start=AsyncMock(), bot=SimpleNamespace(set_webhook=AsyncMock()))
    with patch.object(webhook.client, "create_application", return_value=application) as create, \
            patch.object(webhook.client, "post_init", AsyncMock()):
        assert asyncio.run(webhook.start()) is application
    assert create.call_args.kwargs == {"polling": False}
    url = application.bot.set_webhook.call_args.args[0]
    assert url == "https://desenmascara-api.onrender.com/telegram/webhook"
    assert application.bot.set_webhook.call_args.kwargs["secret_token"] == webhook.secret()


def test_on_render_it_never_starts_on_a_disk_that_is_erased(monkeypatch):
    from app.db import database

    monkeypatch.setattr(settings, "RENDER", True)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        asyncio.run(database.init_db())  # the tests run on SQLite
