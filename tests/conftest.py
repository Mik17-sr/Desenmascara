import os
import tempfile

from cryptography.fernet import Fernet

# Before any app import: settings and the database engine are created when app.* is imported.
_db_dir = tempfile.mkdtemp(prefix="desenmascara-tests-")
os.environ.update({
    # TEST_DATABASE_URL runs the same tests on an empty PostgreSQL with the Supabase migration applied.
    "DATABASE_URL": os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{_db_dir}/test.db",
    "HMAC_SECRET": "test-hmac-secret",
    "ENCRYPTION_KEY": Fernet.generate_key().decode(),
    "BOT_API_SECRET": "test-bot-secret",
    "ADMIN_API_KEY": "test-admin-key",
    "OLLAMA_HOST": "http://127.0.0.1:9",  # nothing listens there: tests never reach a real model
})

from contextlib import contextmanager  # noqa: E402
from unittest.mock import AsyncMock, patch  # noqa: E402

import pytest  # noqa: E402

BOT = {"X-Bot-Secret": "test-bot-secret"}
ADMIN = {"X-Admin-Key": "test-admin-key"}


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    # One client for the session: the async database pool must stay on one event loop.
    with patch("app.main.warm_up", AsyncMock()), patch("app.main.warm_up_models", AsyncMock()):
        with TestClient(app) as test_client:
            yield test_client


@contextmanager
def fake_ai(modalidad="ninguna", pide="nada", presion=False, ages=None):
    """The AI answers with fixed values; RDAP answers 'not registered' unless ages is given."""
    from app.engine.analyzer import Psicologia
    from app.engine.enlaces import DomainAge

    psicologia = None if modalidad is None else Psicologia(modalidad, pide, presion)

    async def domain_ages(domains):
        return ages if ages is not None else {d: DomainAge(d, False) for d in domains}

    with patch("app.engine.cerebro.classify", AsyncMock(return_value=psicologia)) as classify, \
            patch("app.engine.cerebro.enlaces.domain_ages", side_effect=domain_ages):
        yield classify


def persona(telegram_id: int, nombre: str = "Prueba") -> dict:
    return {"telegram_id": telegram_id, "chat_id": telegram_id * 10, "nombre": nombre}


def consenting(client, telegram_id: int, nombre: str = "Prueba") -> dict:
    body = persona(telegram_id, nombre)
    assert client.post("/api/v1/bot/consentimiento", json=body, headers=BOT).status_code == 200
    return body
