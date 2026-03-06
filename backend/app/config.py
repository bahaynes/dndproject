import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "DnD West Marches"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_in_env_file")
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

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
