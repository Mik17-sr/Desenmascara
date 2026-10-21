from pathlib import Path

from app.core.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"


def test_settings_load_env_example():
    # Copying .env.example to .env is the first setup step; the bot's keys must not break the API.
    Settings(_env_file=ENV_EXAMPLE)


def test_bot_token_is_read_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=123:abc\n", encoding="utf-8")
    assert Settings(_env_file=env_file).TELEGRAM_BOT_TOKEN == "123:abc"
