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

    # Comma-separated list of Discord User IDs allowed to setup campaigns
    ADMIN_DISCORD_IDS: str = ""

    # Comma-separated list of Discord role names (case-insensitive) treated as GM/admin
    ADMIN_DISCORD_ROLE_NAMES: str = "GM,DM"

    # Debug token for the /api/debug/* endpoints. Leave empty to disable those endpoints.
    DEBUG_TOKEN: str = ""

    # Environment name — set to "production" to disable dev-only endpoints like /api/auth/dev-token.
    APP_ENV: str = "development"
    ENABLE_DEV_TOKEN: bool = False

    # Additional comma-separated CORS origins beyond FRONTEND_URL
    CORS_ORIGINS: str = ""

    # Shared secret sent by Caddy reverse proxy to Cloud Run backend (optional; disabled when empty)
    PROXY_SHARED_SECRET: str = ""
    PROXY_SHARED_SECRET_PREVIOUS: str = ""

    # In-process sliding-window rate limiter on auth and bake-earth endpoints
    RATE_LIMIT_ENABLED: bool = False

    # LLM Service (OpenRouter)
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "deepseek/deepseek-chat"

    # Map Layer / Tile Storage ("local" for dev, "gcs" for Cloud Run)
    TILE_STORAGE_BACKEND: str = "local"
    LOCAL_TILE_DIR: str = "./data/map_layers"
    GCS_TILE_BUCKET: str = ""

    # MCP server + its OAuth 2.1 authorization server (docs/plans/mcp-oauth.md)
    # Public origin the MCP URL, issuer and Discord callback are built from.
    PUBLIC_ORIGIN: str = "http://localhost:8000"
    # Signs MCP access tokens. Separate from SECRET_KEY so frontend JWTs never validate at /api/mcp.
    MCP_TOKEN_SECRET: str = ""
    # Lifetimes. Ben's numbers to pick; these defaults are placeholders.
    MCP_ACCESS_TOKEN_MINUTES: int = 60
    MCP_REFRESH_TOKEN_DAYS: int = 30
    MCP_AUTH_CODE_SECONDS: int = 300
    MCP_PENDING_AUTH_SECONDS: int = 600
    # Plan question 6: seconds an already-rotated refresh token may be replayed without
    # revoking the whole grant (two instances refreshing at once). 0 = any reuse revokes.
    MCP_REFRESH_REUSE_GRACE_SECONDS: int = 0
    # Defaults to <PUBLIC_ORIGIN>/api/oauth/discord/callback; must be registered in the Discord portal.
    MCP_DISCORD_REDIRECT_URI: str = ""
    # Extra Host header values accepted at /api/mcp (comma-separated; "*.run.app" matches any subdomain),
    # e.g. the Cloud Run host that Caddy sets. The PUBLIC_ORIGIN host and localhost are always allowed.
    MCP_ALLOWED_HOSTS: str = ""
    # Dev/test only: let client ID metadata documents live on http:// or private addresses.
    MCP_CIMD_ALLOW_INSECURE: bool = False

    model_config = SettingsConfigDict(case_sensitive=True, env_file='.env', extra='ignore')

    @property
    def public_origin(self) -> str:
        return self.PUBLIC_ORIGIN.rstrip("/")

    @property
    def mcp_resource_url(self) -> str:
        return f"{self.public_origin}/api/mcp"

    @property
    def mcp_discord_redirect_uri(self) -> str:
        return self.MCP_DISCORD_REDIRECT_URI or f"{self.public_origin}/api/oauth/discord/callback"

    @property
    def mcp_enabled(self) -> bool:
        """Needs MCP_TOKEN_SECRET, except in local development where a derived dev key stands in.
        PR previews stay off: MCP login can't work there (no registered Discord redirect)."""
        return bool(self.MCP_TOKEN_SECRET) or self.APP_ENV == "development"

    @property
    def mcp_token_secret(self) -> str:
        """The MCP signing key. Outside production an unset key falls back to a derived dev key."""
        if self.MCP_TOKEN_SECRET:
            return self.MCP_TOKEN_SECRET
        if self.APP_ENV != "development":
            raise RuntimeError("MCP is disabled: MCP_TOKEN_SECRET is unset")
        return "mcp-dev-only:" + self.SECRET_KEY

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

        # Production security invariants — fail closed
        if self.APP_ENV == "production":
            if self.SECRET_KEY == _DEFAULT_SECRET_KEY or len(self.SECRET_KEY.strip()) < 32:
                logger.critical(
                    "SECRET_KEY must be set to a strong secret (>= 32 characters) in production."
                )
                raise ValueError(
                    "SECRET_KEY must be set to a strong secret (>= 32 characters) when APP_ENV=production."
                )
            if self.ENABLE_DEV_TOKEN:
                logger.critical("ENABLE_DEV_TOKEN cannot be enabled when APP_ENV=production.")
                raise ValueError("ENABLE_DEV_TOKEN cannot be true when APP_ENV=production.")
            if self.MCP_CIMD_ALLOW_INSECURE:
                raise ValueError("MCP_CIMD_ALLOW_INSECURE cannot be true when APP_ENV=production.")
            if self.MCP_TOKEN_SECRET:
                # Set but weak is a mistake worth failing on; unset just leaves MCP off (mcp_enabled).
                if len(self.MCP_TOKEN_SECRET.strip()) < 32 or self.MCP_TOKEN_SECRET == self.SECRET_KEY:
                    logger.critical("MCP_TOKEN_SECRET must be >= 32 characters and differ from SECRET_KEY.")
                    raise ValueError(
                        "MCP_TOKEN_SECRET must be >= 32 characters and not equal to SECRET_KEY when APP_ENV=production."
                    )
                if not self.PUBLIC_ORIGIN.startswith("https://"):
                    raise ValueError("PUBLIC_ORIGIN must be an https:// URL when MCP is enabled in production.")
            else:
                logger.warning("MCP_TOKEN_SECRET is unset: the MCP server and its OAuth endpoints are disabled.")

        # Insecure default secret key (non-production warning)
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
