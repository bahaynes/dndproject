"""MCP access tokens, hashing, scopes and small time helpers."""
import datetime
import hashlib
import secrets
import uuid
from typing import Iterable, Optional

import jwt

from ...config import get_settings

ALGORITHM = "HS256"

SCOPE_READ = "board:read"
SCOPE_WRITE = "board:write"
SUPPORTED_SCOPES = [SCOPE_READ, SCOPE_WRITE]

SCOPE_DESCRIPTIONS = {
    SCOPE_READ: "Read missions, sessions and sign-ups, items and factions.",
    SCOPE_WRITE: "Draft and edit missions (always created hidden) and link them to Foundry one-shots.",
}


def utcnow() -> datetime.datetime:
    """Naive UTC, matching the rest of the schema."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_secret(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def normalize_scopes(scopes: Iterable[str]) -> list[str]:
    """Drops unknown scopes and applies the hierarchy: board:write implies board:read."""
    wanted = {s for s in scopes if s in SUPPORTED_SCOPES}
    if SCOPE_WRITE in wanted:
        wanted.add(SCOPE_READ)
    return [s for s in SUPPORTED_SCOPES if s in wanted]


def scope_string(scopes: Iterable[str]) -> str:
    return " ".join(normalize_scopes(scopes))


def split_scopes(value: Optional[str]) -> list[str]:
    return [s for s in (value or "").split() if s]


def create_access_token(*, user_id: int, campaign_id: int, client_id: str, grant_id: int, scopes: str) -> tuple[str, int]:
    """Returns (jwt, expires_in_seconds)."""
    settings = get_settings()
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_in = settings.MCP_ACCESS_TOKEN_MINUTES * 60
    claims = {
        "iss": settings.public_origin,
        "sub": str(user_id),
        "aud": settings.mcp_resource_url,
        "campaign_id": campaign_id,
        "client_id": client_id,
        "grant_id": grant_id,
        "scope": scopes,
        "iat": now,
        "exp": now + datetime.timedelta(seconds=expires_in),
        "jti": uuid.uuid4().hex,
        "typ": "mcp_access",
    }
    return jwt.encode(claims, settings.mcp_token_secret, algorithm=ALGORITHM), expires_in


def decode_access_token(token: str) -> Optional[dict]:
    """Verifies signature, issuer, audience and expiry. Returns claims or None."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.mcp_token_secret,
            algorithms=[ALGORITHM],
            audience=settings.mcp_resource_url,
            issuer=settings.public_origin,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    if claims.get("typ") != "mcp_access":
        return None
    return claims
