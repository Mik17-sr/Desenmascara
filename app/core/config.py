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
    WHISPER_MODEL: str = "base"
    # Local SQLite when neither is set (see app/db/database.py); a PostgreSQL or Supabase URL also works.
    DATABASE_URL: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None

    # Secrets. scripts/setup_local.py generates them into .env; never commit real values.
    HMAC_SECRET: str = ""
    ENCRYPTION_KEY: str = ""
    BOT_API_SECRET: str = ""
    ADMIN_API_KEY: str = ""

    DASHBOARD_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Optional reputation service; the link check works without it.
    GOOGLE_SAFE_BROWSING_KEY: Optional[str] = None

    # Telegram bot (app/bot/client.py).
    API_BASE_URL: str = "http://127.0.0.1:8000"
    TELEGRAM_BOT_TOKEN: Optional[str] = None

settings = Settings()
