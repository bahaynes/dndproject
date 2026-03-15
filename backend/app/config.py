import os
import logging
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_SECRET_KEY = "a_very_secret_key_that_should_be_in_env_file"

class Settings(BaseSettings):
    PROJECT_NAME: str = "DnD West Marches"
    SECRET_KEY: str = os.getenv("SECRET_KEY", _DEFAULT_SECRET_KEY)
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Frontend Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Discord Configuration
    DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_REDIRECT_URI: str = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5173/api/auth/discord/callback")

    # LLM Configuration
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://openrouter.ai/api/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")

    # ComfyUI Configuration
    COMFYUI_URL: str = os.getenv("COMFYUI_URL", "http://localhost:8188")
    COMFYUI_TIMEOUT: int = int(os.getenv("COMFYUI_TIMEOUT", 300))

    # One-Shot Generator Configuration
    ONESHOT_OUTPUT_DIR: str = os.getenv("ONESHOT_OUTPUT_DIR", "/app/data/oneshots")
    ONESHOT_MAX_CONCURRENT: int = int(os.getenv("ONESHOT_MAX_CONCURRENT", 2))

    # Comma-separated list of Discord User IDs allowed to setup campaigns
    ADMIN_DISCORD_IDS: str = os.getenv("ADMIN_DISCORD_IDS", "")

    # Debug token for the /api/debug/* endpoints. Leave empty to disable those endpoints.
    DEBUG_TOKEN: str = os.getenv("DEBUG_TOKEN", "")

    # Environment name — set to "production" to disable dev-only endpoints like /api/auth/dev-token.
    APP_ENV: str = os.getenv("APP_ENV", "development")

    class Config:
        case_sensitive = True

    @model_validator(mode="after")
    def validate_and_log_startup_config(self) -> "Settings":
        logger = logging.getLogger("app.config")

        # Missing critical secrets
        missing = []
        if not self.DISCORD_CLIENT_ID:
            missing.append("DISCORD_CLIENT_ID")
        if not self.DISCORD_CLIENT_SECRET:
            missing.append("DISCORD_CLIENT_SECRET")
        if missing:
            logger.error("Missing required env vars — Discord OAuth will not work: %s", missing)

        # Insecure default secret key
        if self.SECRET_KEY == _DEFAULT_SECRET_KEY:
            logger.warning(
                "SECRET_KEY is using the insecure default value — set SECRET_KEY in your .env"
            )

        # Effective redirect URI — this is the most common source of Discord OAuth failures.
        # Compare this value against what is registered in the Discord Developer Portal.
        if not self.DISCORD_REDIRECT_URI:
            logger.error("DISCORD_REDIRECT_URI is not set — Discord OAuth callback will fail")
        else:
            logger.info(
                "Discord OAuth redirect URI: %s",
                self.DISCORD_REDIRECT_URI,
                extra={"discord_redirect_uri": self.DISCORD_REDIRECT_URI},
            )
            if ":5173" in self.DISCORD_REDIRECT_URI:
                logger.warning(
                    "DISCORD_REDIRECT_URI contains port 5173 (the frontend dev server). "
                    "Discord calls back to the backend — the URI should point at the backend "
                    "port (8000 in dev, 80/443 in prod via the reverse proxy).",
                    extra={"discord_redirect_uri": self.DISCORD_REDIRECT_URI},
                )

        return self


@lru_cache()
def get_settings():
    return Settings()
