"""Fingerprints, encryption and access checks shared by the API and the bot."""

import hashlib
import hmac
import re
import secrets

from cryptography.fernet import Fernet
from fastapi import Header, HTTPException

from app.core.config import settings

SETUP_HINT = "Ejecuta `python scripts/setup_local.py` para generar los secretos en .env."


def _secret(name: str) -> str:
    value = getattr(settings, name)
    if not value:
        raise RuntimeError(f"Falta {name}. {SETUP_HINT}")
    return value


def fingerprint(value: str) -> str:
    """HMAC-SHA256 of a phone, key or Telegram id: searchable without storing the value."""
    return hmac.new(_secret("HMAC_SECRET").encode(), value.encode(), hashlib.sha256).hexdigest()


def encrypt(value: str) -> str:
    return Fernet(_secret("ENCRYPTION_KEY").encode()).encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return Fernet(_secret("ENCRYPTION_KEY").encode()).decrypt(token.encode()).decode()


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def new_api_key() -> str:
    return "sec_live_" + secrets.token_urlsafe(24)


def normalize_phone(raw: str) -> str | None:
    """Colombian numbers to E.164 digits without '+': '310 000 0000' -> '573100000000'."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10 and digits[0] in "36":
        digits = "57" + digits
    if 10 <= len(digits) <= 15:
        return digits
    return None


def mask_value(value: str, tipo: str) -> str:
    """'573150000000' -> '+57 315 ••• 0000', so lists never show a full number."""
    if tipo == "telefono" and value.startswith("57") and len(value) == 12:
        return f"+57 {value[2:5]} ••• {value[-4:]}"
    if tipo == "enlace":
        return value
    if len(value) <= 4:
        return "•" * len(value)
    return f"{value[:3]} ••• {value[-4:]}" if len(value) > 7 else f"••• {value[-4:]}"


def _matches(given: str | None, expected_name: str) -> bool:
    expected = _secret(expected_name)
    return bool(given) and hmac.compare_digest(given, expected)


async def require_bot(x_bot_secret: str | None = Header(default=None)) -> None:
    """Endpoints that act for a Telegram user: only the bot process holds this secret."""
    if not _matches(x_bot_secret, "BOT_API_SECRET"):
        raise HTTPException(status_code=401, detail="No autorizado.")


async def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Team-only actions: review requests and the official-number list."""
    if not _matches(x_admin_key, "ADMIN_API_KEY"):
        raise HTTPException(status_code=401, detail="No autorizado.")
