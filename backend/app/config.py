import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    PROJECT_NAME: str = "DnD West Marches"
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_env_file"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "sqlite:///./test.db"

    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:5173"

    # Discord Configuration
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_REDIRECT_URI: str = "http://localhost:5173/api/auth/discord/callback"

    # LLM Configuration
    LLM_API_BASE: str = "https://openrouter.ai/api/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek/deepseek-chat"

    # ComfyUI Configuration
    COMFYUI_URL: str = "http://localhost:8188"
    COMFYUI_TIMEOUT: int = 300

    # One-Shot Generator Configuration
    ONESHOT_OUTPUT_DIR: str = "/app/data/oneshots"
    ONESHOT_MAX_CONCURRENT: int = 2

    # Comma-separated list of Discord User IDs allowed to setup campaigns
    ADMIN_DISCORD_IDS: str = ""

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


_WARN_IF_EMPTY = {
    "DISCORD_CLIENT_ID": "Discord auth will not work",
    "DISCORD_CLIENT_SECRET": "Discord auth will not work",
    "LLM_API_KEY": "LLM/oneshot features will not work",
    "DATABASE_URL": "database connection will use SQLite fallback",
}


def validate_settings(settings: Settings) -> None:
    for var, consequence in _WARN_IF_EMPTY.items():
        value = getattr(settings, var)
        if not value or value == Settings.model_fields[var].default:
            logger.warning("ENV VAR NOT SET or using default: %s — %s", var, consequence)


@lru_cache()
def get_settings():
    return Settings()
