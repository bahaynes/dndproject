import hmac
import logging
import re
import secrets
from datetime import timedelta
from typing import Optional
from urllib.parse import urlencode, urlparse

import httpx
import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ... import security
from ...config import get_settings
from ...dependencies import get_current_active_user, get_current_user_global, get_db
from ..campaigns import service as campaign_service
from . import models, schemas, service as crud

logger = logging.getLogger("app.auth")

router = APIRouter()

_PR_CALLBACK_HOST_RE = re.compile(
    r"dnd-frontend-pr-\d+-(?:[a-z0-9-]+-uc\.a|\d+\.us-central1)\.run\.app"
)


def _dev_login_allowed(settings) -> bool:
    return bool(
        settings.ENABLE_DEV_TOKEN
        and settings.APP_ENV != "production"
        and len(settings.DEV_LOGIN_SECRET.strip()) >= 32
    )


def _dev_login_secret_ok(settings, provided: Optional[str]) -> bool:
    if not provided:
        return False
    return hmac.compare_digest(
        provided.encode("utf-8"), settings.DEV_LOGIN_SECRET.strip().encode("utf-8")
    )


def _is_safe_return_to(return_to: str, settings) -> bool:
    if not return_to or any(ch in return_to for ch in ("\r", "\n", "\\")):
        return False
    if return_to.startswith("/"):
        return not return_to.startswith("//")
    try:
        parsed = urlparse(return_to)
    except Exception:
        return False
    hostname = parsed.hostname
    if not hostname or parsed.username is not None or parsed.password is not None:
        return False
    if hostname == "localhost" and settings.APP_ENV != "production":
        return parsed.scheme in ("http", "https")
    allowed_hosts = {"westmarches.bahaynes.com", "dndproject.bahaynes.com"}
    if settings.FRONTEND_URL:
        frontend_host = urlparse(settings.FRONTEND_URL).hostname
        if frontend_host:
            allowed_hosts.add(frontend_host)
    return parsed.scheme == "https" and hostname in allowed_hosts


def _is_allowed_proxy_callback(callback_url: str, app_env: str) -> bool:
    if not callback_url:
        return False
    try:
        parsed = urlparse(callback_url)
    except Exception:
        return False
    if (
        parsed.path != "/api/auth/discord/callback"
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    if hostname == "localhost" and app_env != "production":
        return parsed.scheme in ("http", "https")
    if parsed.scheme != "https":
        return False
    if hostname in ("westmarches.bahaynes.com", "dndproject.bahaynes.com"):
        return True
    return bool(_PR_CALLBACK_HOST_RE.fullmatch(hostname))


@router.get("/discord/login", tags=["Authentication"])
async def login_via_discord(
    request: Request,
    return_to: Optional[str] = None,
):
    """
    Redirects the user to Discord OAuth2 login page.
    Optionally accepts a 'return_to' query param to redirect back to a specific frontend URL.
    """
    settings = get_settings()
    safe_return_to = return_to if (return_to and _is_safe_return_to(return_to, settings)) else None

    if settings.APP_ENV == "production" and settings.FRONTEND_URL:
        frontend_host = urlparse(settings.FRONTEND_URL).hostname
        forwarded_host = (
            request.headers.get("X-Forwarded-Host", "")
            .split(",", 1)[0]
            .strip()
            .split(":", 1)[0]
            .lower()
        )
        if frontend_host and forwarded_host and forwarded_host != frontend_host.lower():
            target = f"{settings.FRONTEND_URL.rstrip('/')}/api/auth/discord/login"
            if safe_return_to:
                target = f"{target}?{urlencode({'return_to': safe_return_to})}"
            return RedirectResponse(url=target)

    scope = "identify guilds"
    nonce = secrets.token_urlsafe(32)

    my_callback_url = f"{settings.FRONTEND_URL.rstrip('/')}/api/auth/discord/callback"
    state_payload: dict[str, str] = {
        "type": "oauth_state",
        "nonce": nonce,
        "callback": my_callback_url,
    }
    if safe_return_to:
        state_payload["return_to"] = safe_return_to

    state_str = security.create_access_token(
        data=state_payload,
        expires_delta=timedelta(minutes=10),
    )

    query = urlencode({
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": scope,
        "state": state_str,
        # Skip Discord's approval screen for users who already authorized the app.
        "prompt": "none",
    })
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?{query}"

    logger.info(
        "Initiating Discord OAuth redirect",
        extra={
            "discord_client_id": settings.DISCORD_CLIENT_ID,
            "redirect_uri": settings.DISCORD_REDIRECT_URI,
        },
    )

    is_prod = settings.APP_ENV == "production"
    response = RedirectResponse(url=discord_auth_url)
    response.set_cookie(
        key="oauth_state_nonce",
        value=nonce,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        path="/api/auth",
    )

    if safe_return_to:
        response.set_cookie(
            key="auth_return_to",
            value=safe_return_to,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=is_prod,
            path="/api/auth",
        )

    return response


@router.get("/discord/proxy-callback", tags=["Authentication"])
async def discord_proxy_callback(code: str, state: str):
    """
    Proxy endpoint to allow PR environments to authenticate via Discord.
    Discord redirect URI must be a fixed URL (production).
    This endpoint receives the callback and forwards it to the PR environment specified in the state.
    """
    settings = get_settings()
    try:
        state_data = jwt.decode(state, options={"verify_signature": False})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state")

    if not isinstance(state_data, dict) or state_data.get("type") != "oauth_state":
        raise HTTPException(status_code=400, detail="Invalid state")

    callback_url = state_data.get("callback")
    if not isinstance(callback_url, str) or not callback_url:
        raise HTTPException(status_code=400, detail="Missing callback URL in state")

    if not _is_allowed_proxy_callback(callback_url, settings.APP_ENV):
        raise HTTPException(status_code=400, detail="Invalid callback domain")

    query_params = urlencode({"code": code, "state": state})
    return RedirectResponse(url=f"{callback_url}?{query_params}")


@router.get("/discord/callback", tags=["Authentication"])
async def discord_callback(
    code: str,
    request: Request,
    response: Response,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Handles the callback from Discord, exchanges code for token, and gets user info.
    Sets a short-lived HttpOnly exchange cookie and redirects to the frontend callback page.
    """
    settings = get_settings()

    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")

    try:
        state_data = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except (ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if state_data.get("type") != "oauth_state":
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    state_nonce = state_data.get("nonce")
    cookie_nonce = request.cookies.get("oauth_state_nonce")
    if (
        not isinstance(state_nonce, str)
        or not state_nonce
        or not cookie_nonce
        or not hmac.compare_digest(state_nonce, cookie_nonce)
    ):
        raise HTTPException(status_code=400, detail="OAuth state mismatch")

    logger.info("Discord OAuth callback received", extra={"code_present": bool(code)})

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_response.status_code != 200:
        logger.error(
            "Discord token exchange failed",
            extra={
                "status_code": token_response.status_code,
                "discord_error": token_response.text,
                "redirect_uri_used": settings.DISCORD_REDIRECT_URI,
            },
        )
        raise HTTPException(status_code=400, detail="Failed to retrieve token from Discord")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    logger.info("Discord token exchange succeeded")

    # Get User Info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if user_response.status_code != 200:
        logger.error(
            "Discord user info fetch failed",
            extra={
                "status_code": user_response.status_code,
                "discord_error": user_response.text,
            },
        )
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Discord")

    discord_user = user_response.json()
    discord_id = discord_user.get("id")
    username = discord_user.get("username")
    avatar = discord_user.get("avatar")

    logger.info(
        "Discord user info retrieved",
        extra={"discord_id": discord_id, "username": username},
    )

    exchange_token = security.create_access_token(
        data={
            "sub": discord_id,
            "type": "oauth_exchange",
            "username": username,
            "avatar": avatar,
            "discord_token": access_token,
        },
        expires_delta=timedelta(minutes=2),
    )

    frontend_url = f"{settings.FRONTEND_URL.rstrip('/')}/login/callback"
    redirect = RedirectResponse(url=frontend_url)
    redirect.set_cookie(
        key="oauth_exchange",
        value=exchange_token,
        max_age=120,
        httponly=True,
        samesite="lax",
        secure=(settings.APP_ENV == "production"),
        path="/api/auth",
    )
    redirect.delete_cookie("oauth_state_nonce", path="/api/auth")
    redirect.delete_cookie("auth_return_to", path="/api/auth")

    return redirect


@router.post("/exchange", tags=["Authentication"])
async def exchange_oauth_cookie(request: Request, response: Response):
    """
    Exchanges the short-lived HttpOnly oauth_exchange cookie for a global JWT
    and Discord access token without exposing credentials in URL query strings.
    """
    settings = get_settings()
    exchange_cookie = request.cookies.get("oauth_exchange")
    if not exchange_cookie:
        raise HTTPException(status_code=401, detail="Missing OAuth exchange session")

    try:
        payload = jwt.decode(
            exchange_cookie,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except (ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid or expired OAuth exchange session")

    discord_id = payload.get("sub")
    if payload.get("type") != "oauth_exchange" or not discord_id:
        raise HTTPException(status_code=401, detail="Invalid OAuth exchange session")

    jwt_token = security.create_access_token(
        data={
            "sub": discord_id,
            "type": "global",
            "username": payload.get("username"),
            "avatar": payload.get("avatar"),
        }
    )

    response.delete_cookie("oauth_exchange", path="/api/auth")
    return {
        "token": jwt_token,
        "discord_token": payload.get("discord_token"),
    }


@router.get("/me", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@router.get("/me/global", tags=["Users"])
async def read_users_me_global(payload: dict = Depends(get_current_user_global)):
    """
    Returns the Discord user info from the global token.
    Used when the user is authenticated with Discord but hasn't selected a campaign yet.
    """
    discord_id = payload.get("sub")
    avatar_hash = payload.get("avatar")
    avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png" if avatar_hash else None

    return {
        "username": payload.get("username"),
        "discord_id": discord_id,
        "avatar_url": avatar_url
    }


class DevTokenRequest(BaseModel):
    discord_id: str = "e2e_player_001"
    username: str = "E2E Player"
    role: str = "player"
    campaign_guild_id: str = "e2e-test-guild"
    campaign_name: str = "E2E Test Campaign"


@router.get("/dev-status", include_in_schema=False)
async def dev_status():
    """
    Returns whether dev login is enabled (requires ENABLE_DEV_TOKEN=true and APP_ENV != production).
    """
    settings = get_settings()
    return {"dev_login_enabled": _dev_login_allowed(settings)}


@router.post("/dev-token", include_in_schema=False)
async def dev_token(
    request: DevTokenRequest,
    db: Session = Depends(get_db),
    x_dev_login_secret: Optional[str] = Header(default=None, alias="X-Dev-Login-Secret"),
):
    """
    Dev-only endpoint for e2e testing. Returns a valid campaign-scoped JWT,
    creating the campaign and user in the database if they don't exist.
    Disabled (404) unless ENABLE_DEV_TOKEN=true, APP_ENV != production, and the
    X-Dev-Login-Secret header matches DEV_LOGIN_SECRET. A wrong or missing secret
    also gets 404, so the endpoint's existence isn't confirmed.
    """
    settings = get_settings()
    if not _dev_login_allowed(settings):
        raise HTTPException(status_code=404, detail="Not found")
    if not _dev_login_secret_ok(settings, x_dev_login_secret):
        logger.warning("Dev login rejected: missing or wrong secret")
        raise HTTPException(status_code=404, detail="Not found")

    from ..campaigns import schemas as campaign_schemas
    from ..characters import models as char_models

    # Get or create campaign
    campaign = campaign_service.get_campaign_by_guild_id(db, request.campaign_guild_id)
    if not campaign:
        campaign = campaign_service.create_campaign(
            db,
            campaign_schemas.CampaignCreate(
                name=request.campaign_name,
                discord_guild_id=request.campaign_guild_id,
            ),
        )

    # Get or create user
    user = crud.get_user_by_discord_id(db, request.discord_id, campaign.id)
    if not user:
        user = crud.create_user(
            db,
            schemas.UserCreate(
                discord_id=request.discord_id,
                username=request.username,
                campaign_id=campaign.id,
                role=request.role,
            ),
        )
        # create_user builds a character but doesn't set active_character_id
        if user.characters and not user.active_character_id:
            user.active_character_id = user.characters[0].id
            db.commit()
            db.refresh(user)
    elif user.role != request.role:
        user.role = request.role
        db.commit()

    token = security.create_access_token(
        data={"sub": request.discord_id, "campaign_id": campaign.id, "role": request.role},
        expires_delta=timedelta(days=7),
    )
    return {"access_token": token, "token_type": "bearer", "campaign_id": campaign.id}
