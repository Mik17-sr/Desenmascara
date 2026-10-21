from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env.example also lists the bot's variables; ignore keys this class does not declare.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Desenmascara API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    # Accept either a direct async PostgreSQL URL or Supabase's database URL.
    DATABASE_URL: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None

settings = Settings()
