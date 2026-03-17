"""
Debug endpoints for AI-assisted troubleshooting.

Protected by X-Debug-Token header matching settings.DEBUG_TOKEN.
If DEBUG_TOKEN is not set, all endpoints return 404 (hidden).

Usage:
    curl -H "X-Debug-Token: <your-token>" http://localhost:8000/api/debug/config
    curl -H "X-Debug-Token: <your-token>" http://localhost:8000/api/debug/health
    curl -X POST -H "X-Debug-Token: <your-token>" -H "Content-Type: application/json" \\
         -d '{"token": "<jwt>"}' http://localhost:8000/api/debug/auth-trace
"""
import re
import logging
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from ...config import get_settings
from ...dependencies import get_db
from ...modules.auth import models as auth_models

logger = logging.getLogger("app.debug")

router = APIRouter(tags=["Debug"])


def require_debug_token(x_debug_token: Optional[str] = Header(None)):
    settings = get_settings()
    if not settings.DEBUG_TOKEN:
        # Hide the existence of debug endpoints when no token is configured.
        raise HTTPException(status_code=404, detail="Not found")
    if x_debug_token != settings.DEBUG_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/config", dependencies=[Depends(require_debug_token)])
async def debug_config():
    """
    Show which environment variables are set, the effective Discord redirect URI,
    and the masked database URL. Safe to share — no secrets are exposed.
    """
    settings = get_settings()
    db_url = settings.DATABASE_URL
    masked_db = re.sub(r":[^/@]+@", ":***@", db_url)

    return {
        "env_vars_set": {
            "DISCORD_CLIENT_ID": bool(settings.DISCORD_CLIENT_ID),
            "DISCORD_CLIENT_SECRET": bool(settings.DISCORD_CLIENT_SECRET),
            "DISCORD_BOT_TOKEN": bool(settings.DISCORD_BOT_TOKEN),
            "SECRET_KEY_is_default": settings.SECRET_KEY == "a_very_secret_key_that_should_be_in_env_file",
            "LLM_API_KEY": bool(settings.LLM_API_KEY),
        },
        # This is the value actually used when building the OAuth redirect URL.
        # Compare it against what is registered in Discord Developer Portal → OAuth2 → Redirects.
        "discord_redirect_uri": settings.DISCORD_REDIRECT_URI,
        "frontend_url": settings.FRONTEND_URL,
        "database_url_masked": masked_db,
        "admin_discord_ids_set": bool(settings.ADMIN_DISCORD_IDS),
    }


@router.get("/health", dependencies=[Depends(require_debug_token)])
async def debug_health(db: Session = Depends(get_db)):
    """
    Check database connectivity and Discord API reachability.
    """
    db_ok = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)
        logger.error("Debug health: DB check failed", extra={"error": db_error})

    discord_ok = False
    discord_error = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("https://discord.com/api/v10/gateway")
            discord_ok = r.status_code == 200
            if not discord_ok:
                discord_error = f"HTTP {r.status_code}"
    except Exception as exc:
        discord_error = str(exc)
        logger.error("Debug health: Discord API unreachable", extra={"error": discord_error})

    return {
        "database": {"ok": db_ok, "error": db_error},
        "discord_api": {"reachable": discord_ok, "error": discord_error},
    }


class AuthTraceRequest(BaseModel):
    token: str


@router.post("/auth-trace", dependencies=[Depends(require_debug_token)])
async def debug_auth_trace(body: AuthTraceRequest, db: Session = Depends(get_db)):
    """
    Walk through JWT validation step by step and return exactly where it fails.
    Useful for diagnosing 401 errors without reading container logs.

    Pass the raw JWT token from the Authorization header (without "Bearer ").
    """
    settings = get_settings()
    steps = []

    # Step 1: JWT decode
    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        steps.append({
            "step": "jwt_decode",
            "ok": True,
            "payload_keys": list(payload.keys()),
            "token_type": payload.get("type"),
        })
    except ExpiredSignatureError:
        steps.append({"step": "jwt_decode", "ok": False, "error": "token_expired"})
        return {"steps": steps, "verdict": "FAIL"}
    except JWTError as exc:
        steps.append({"step": "jwt_decode", "ok": False, "error": str(exc)})
        return {"steps": steps, "verdict": "FAIL"}

    # Step 2: Required claims
    discord_id = payload.get("sub")
    campaign_id = payload.get("campaign_id")
    token_type = payload.get("type")

    steps.append({
        "step": "claims_check",
        "ok": bool(discord_id),
        "has_sub": bool(discord_id),
        "has_campaign_id": campaign_id is not None,
        "token_type": token_type,
    })

    if not discord_id:
        return {"steps": steps, "verdict": "FAIL — missing 'sub' claim"}

    if campaign_id is None:
        return {
            "steps": steps,
            "verdict": "FAIL — this is a global token (no campaign_id). "
                       "Use it on /api/auth/me/global or exchange it for a campaign token first.",
        }

    # Step 3: DB user lookup
    user = db.query(auth_models.User).filter(
        auth_models.User.discord_id == discord_id,
        auth_models.User.campaign_id == campaign_id,
    ).first()

    if user:
        steps.append({
            "step": "user_lookup",
            "ok": True,
            "user_id": user.id,
            "is_active": user.is_active,
            "role": user.role,
            "has_active_character": user.active_character_id is not None,
        })
        verdict = "OK" if user.is_active else "FAIL — user is inactive"
    else:
        steps.append({
            "step": "user_lookup",
            "ok": False,
            "error": "no_user_found",
            "discord_id": discord_id,
            "campaign_id": campaign_id,
        })
        verdict = "FAIL — no user found for this discord_id + campaign_id combination"

    return {"steps": steps, "verdict": verdict}
