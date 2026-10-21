from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt, encrypt, fingerprint, normalize_phone
from app.db.models import Usuario, utcnow


def value_fingerprint(tipo: str, valor: str) -> str:
    """One namespace per kind of value, shared by users, calls, the Banco and the whitelist."""
    return fingerprint(f"{tipo}:{valor}")


async def by_telegram(session: AsyncSession, telegram_id: int) -> Usuario | None:
    return await session.scalar(select(Usuario).where(Usuario.telegram_hash == value_fingerprint("telegram", str(telegram_id))))


async def get_or_create(session: AsyncSession, telegram_id: int, chat_id: int, nombre: str | None = None) -> Usuario:
    user = await by_telegram(session, telegram_id)
    if user is None:
        user = Usuario(
            telegram_hash=value_fingerprint("telegram", str(telegram_id)),
            chat_cifrado=encrypt(str(chat_id)),
            nombre_corto=(nombre or "").strip()[:60] or None,
        )
        session.add(user)
        await session.flush()
    return user


def chat_id_of(user: Usuario) -> int:
    return int(decrypt(user.chat_cifrado))


async def set_phone(session: AsyncSession, user: Usuario, raw_phone: str) -> str:
    """Store the fingerprint of the person's own number, shared through Telegram's contact button."""
    phone = normalize_phone(raw_phone)
    if phone is None:
        raise ValueError("Número no válido")
    phone_hash = value_fingerprint("telefono", phone)
    # A number belongs to one account: if it moved to a new Telegram account, the old one loses it.
    await session.execute(update(Usuario).where(Usuario.telefono_hash == phone_hash, Usuario.id != user.id).values(telefono_hash=None))
    user.telefono_hash = phone_hash
    return phone


def set_consent(user: Usuario) -> None:
    if user.consentimiento_at is None:
        user.consentimiento_at = utcnow()
