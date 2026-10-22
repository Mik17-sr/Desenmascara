"""Fingerprints, encryption and access checks shared by the API and the bot."""

import hashlib
import hmac
import re
import secrets
import time

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


# Entity panel sign-in: e-mail and password. scrypt makes each guess slow; only the hash is stored.
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


def new_password() -> str:
    return secrets.token_urlsafe(9)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT).hex()}"


def password_matches(password: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$")
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT).hex()
    except ValueError:
        return False
    return hmac.compare_digest(candidate, digest)


def new_session(entity_id: str, hours: int) -> str:
    """A signed panel session: 'ses_<entity>.<expiry>.<signature>'. Nothing is stored server-side."""
    payload = f"{entity_id}.{int(time.time()) + hours * 3600}"
    return f"ses_{payload}.{_session_signature(payload)}"


def session_entity_id(token: str) -> str | None:
    """The entity of a valid, unexpired session; None for anything else."""
    try:
        entity_id, expires, signature = token.removeprefix("ses_").split(".")
        valid = token.startswith("ses_") and int(expires) > time.time()
    except ValueError:
        return None
    return entity_id if valid and hmac.compare_digest(signature, _session_signature(f"{entity_id}.{expires}")) else None


def _session_signature(payload: str) -> str:
    return hmac.new(_secret("HMAC_SECRET").encode(), b"panel-entidad:" + payload.encode(), hashlib.sha256).hexdigest()


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
