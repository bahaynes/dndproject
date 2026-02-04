from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
from typing import Optional
from ...config import get_settings

from ... import security
from ...dependencies import get_db, get_current_user
from . import schemas, service as crud, models
from ..campaigns import service as campaign_service

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

    response = RedirectResponse(url=discord_auth_url)

    # Validate and store return_to in a cookie if provided
    if return_to:
        # Simple validation: allow localhost, *.vercel.app, and the production domain
        allowed_domains = ["localhost", ".vercel.app", "westmarches.bahaynes.com"]
        is_allowed = False
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
        raise HTTPException(status_code=400, detail="Failed to retrieve token from Discord")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    # Get User Info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Discord")

    discord_user = user_response.json()
    discord_id = discord_user.get("id")
    username = discord_user.get("username")
    avatar = discord_user.get("avatar")

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

    if return_to:
        base_url = return_to

    # Redirect to frontend with token
    frontend_url = f"{base_url}/login/callback?token={jwt_token}&discord_token={access_token}"

    redirect = RedirectResponse(url=frontend_url)
    if return_to:
        redirect.delete_cookie("auth_return_to")

    return redirect


@router.get("/me", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
