from pathlib import Path

from app.core.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"


def test_settings_load_env_example():
    # Copying .env.example to .env is the first setup step; the bot's keys must not break the API.
    Settings(_env_file=ENV_EXAMPLE)
