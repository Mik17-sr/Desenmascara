from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Desenmascara API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    OLLAMA_HOST: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    # Accept either a direct async PostgreSQL URL or Supabase's database URL.
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    SUPABASE_DB_URL: Optional[str] = Field(default=None, env="SUPABASE_DB_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
