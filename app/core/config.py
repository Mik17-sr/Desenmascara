from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Ignore keys this class does not declare, such as those for other services the README lists.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Desenmascara API"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"

    # 127.0.0.1 rather than localhost: on Windows, localhost tries IPv6 first and adds ~0.2 s per connection.
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.2"
    # False where there is no Ollama (Render): the rules answer alone, as calibrated, instead of "no concluyente".
    IA_LOCAL: bool = True
    WHISPER_MODEL: str = "base"
    # Load OCR and Whisper before serving. False on a small server (Render free: 512 MB, and it must wake fast):
    # each model then loads with its first screenshot or voice note.
    PRECARGAR_MODELOS: bool = True
    # Local SQLite when neither is set (see app/db/database.py); a PostgreSQL or Supabase URL also works.
    DATABASE_URL: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None

    # Secrets. scripts/setup_local.py generates them into .env; never commit real values.
    HMAC_SECRET: str = ""
    ENCRYPTION_KEY: str = ""
    BOT_API_SECRET: str = ""
    ADMIN_API_KEY: str = ""

    DASHBOARD_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Optional reputation services; the link check works without them.
    GOOGLE_SAFE_BROWSING_KEY: Optional[str] = None
    URLHAUS_AUTH_KEY: Optional[str] = None

    # Telegram bot (app/bot/client.py).
    API_BASE_URL: str = "http://127.0.0.1:8000"
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    # How long the bot waits for a screenshot or a voice note; a slow server needs more.
    BOT_TIMEOUT_IMAGEN: float = 20.0
    BOT_TIMEOUT_VOZ: float = 30.0
    # With a public address the bot runs inside the API by webhook (app/bot/webhook.py) instead of polling.
    # Render sets RENDER_EXTERNAL_URL by itself; TELEGRAM_WEBHOOK_URL is for any other server.
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    RENDER_EXTERNAL_URL: Optional[str] = None
    # Render sets RENDER=true. There the disk is erased on every restart, so SQLite is refused (app/db/database.py).
    RENDER: bool = False

settings = Settings()
