import os
import logging
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_SECRET_KEY = "a_very_secret_key_that_should_be_in_env_file"

class Settings(BaseSettings):
    PROJECT_NAME: str = "DnD West Marches"
    SECRET_KEY: str = _DEFAULT_SECRET_KEY
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

    # Debug token for the /api/debug/* endpoints. Leave empty to disable those endpoints.
    DEBUG_TOKEN: str = ""

    # Environment name — set to "production" to disable dev-only endpoints like /api/auth/dev-token.
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(case_sensitive=True, env_file='.env', extra='ignore')

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

        if not self.DATABASE_URL:
            logger.critical("DATABASE_URL is empty in settings. The application cannot start without a valid database connection string.")
            raise ValueError("DATABASE_URL environment variable is empty. Please check your configuration and secrets.")

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
