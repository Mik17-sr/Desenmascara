"""Create .env from .env.example and fill in the secrets that are empty. Safe to run again.

    python scripts/setup_local.py

It never prints the secrets: open .env to see them (ADMIN_API_KEY is the team key for the Dashboard).
"""

import secrets
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parent.parent
GENERATORS = {
    "HMAC_SECRET": lambda: secrets.token_hex(32),
    "ENCRYPTION_KEY": lambda: Fernet.generate_key().decode(),
    "BOT_API_SECRET": lambda: secrets.token_urlsafe(32),
    "ADMIN_API_KEY": lambda: "adm_" + secrets.token_urlsafe(24),
}


def main() -> None:
    env = ROOT / ".env"
    source = env if env.exists() else ROOT / ".env.example"
    lines, seen, generated = [], set(), []
    for line in source.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        key = key.strip()
        if sep and not line.lstrip().startswith("#") and key in GENERATORS:
            seen.add(key)
            if not value.strip():
                line = f"{key}={GENERATORS[key]()}"
                generated.append(key)
        lines.append(line)
    for key, make in GENERATORS.items():
        if key not in seen:
            lines.append(f"{key}={make()}")
            generated.append(key)
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f".env listo en {env}")
    print("Secretos generados: " + (", ".join(generated) if generated else "ninguno (ya existían)"))
    print("Si cambias HMAC_SECRET o ENCRYPTION_KEY, los datos guardados dejan de servir: borra desenmascara.db.")


if __name__ == "__main__":
    main()
