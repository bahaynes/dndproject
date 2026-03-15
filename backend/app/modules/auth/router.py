import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx
from typing import Optional
from ...config import get_settings

from ... import security
from ...dependencies import get_db, get_current_user, get_current_user_global
from . import schemas, service as crud, models
from ..campaigns import service as campaign_service

logger = logging.getLogger("app.auth")

router = APIRouter()
settings = get_settings()

@router.get("/discord/login", tags=["Authentication"])
async def login_via_discord(
    return_to: Optional[str] = None,
):
    """
    Redirects the user to Discord OAuth2 login page.
    Optionally accepts a 'return_to' query param to redirect back to a specific frontend URL (e.g. Vercel preview).
    """
    scope = "identify guilds"
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope}"
    )

    logger.info(
        "Initiating Discord OAuth redirect",
        extra={
            "discord_client_id": settings.DISCORD_CLIENT_ID,
            "redirect_uri": settings.DISCORD_REDIRECT_URI,
        },
    )

    response = RedirectResponse(url=discord_auth_url)

    # Validate and store return_to in a cookie if provided
    if return_to:
        # Simple validation: allow localhost, *.vercel.app, and the production domain
        allowed_domains = ["localhost", ".vercel.app", "westmarches.bahaynes.com"]
        is_allowed = False

        if return_to.startswith("/"):
            is_allowed = True
        else:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(return_to)
                hostname = parsed.hostname
                if hostname:
                    for domain in allowed_domains:
                        if domain.startswith("."): # wildcard
                            if hostname.endswith(domain):
                                is_allowed = True
                                break
                        elif hostname == domain:
                            is_allowed = True
                            break
            except Exception:
                pass

        if is_allowed:
             # Set cookie for 5 minutes
            response.set_cookie(
                key="auth_return_to",
                value=return_to,
                max_age=300,
                httponly=True,
                samesite="lax",
                secure=False # Set to True in production if using https, but lax works mostly
            )

    return response


@router.get("/discord/callback", tags=["Authentication"])
async def discord_callback(code: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Handles the callback from Discord, exchanges code for token, and gets user info.
    Returns a temporary token that allows the user to list/select campaigns.
    """
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
                # Discord returns a JSON body with error + error_description — this is the key diagnostic.
                # e.g. {"error": "invalid_grant", "error_description": "Invalid \"redirect_uri\" in request."}
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

    # We construct a special token payload
    token_payload = {
        "sub": discord_id,
        "type": "global",
        "username": username,
        "avatar": avatar,
    }

    jwt_token = security.create_access_token(data=token_payload)

    # Determine redirect URL
    return_to = request.cookies.get("auth_return_to")
    base_url = settings.FRONTEND_URL

    # Redirect to frontend with token
    frontend_url = f"{base_url}/login/callback?token={jwt_token}&discord_token={access_token}"

    if return_to:
        from urllib.parse import quote
        frontend_url += f"&next={quote(return_to)}"

    redirect = RedirectResponse(url=frontend_url)
    if return_to:
        redirect.delete_cookie("auth_return_to")

    return redirect


@router.get("/me", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
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


@router.post("/dev-token", include_in_schema=False)
async def dev_token(
    request: DevTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Dev-only endpoint for e2e testing. Returns a valid campaign-scoped JWT,
    creating the campaign and user in the database if they don't exist.
    Disabled (404) when APP_ENV=production.
    """
    if settings.APP_ENV == "production":
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
        data={"sub": request.discord_id, "campaign_id": campaign.id, "role": request.role}
    )
    return {"access_token": token, "token_type": "bearer", "campaign_id": campaign.id}
