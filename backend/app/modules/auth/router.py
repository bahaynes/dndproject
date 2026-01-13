from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
from ...config import get_settings

from ... import security
from ...dependencies import get_db, get_current_user
from . import schemas, service as crud
from ..campaigns import service as campaign_service

router = APIRouter()
settings = get_settings()

@router.get("/discord/login", tags=["Authentication"])
async def login_via_discord():
    """
    Redirects the user to Discord OAuth2 login page.
    """
    scope = "identify guilds"
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope}"
    )
    return RedirectResponse(url=discord_auth_url)


@router.get("/discord/callback", tags=["Authentication"])
async def discord_callback(code: str, db: Session = Depends(get_db)):
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

    # Check if user exists in ANY campaign to maybe auto-login if only one?
    # For now, we issue a "Global Token" (Discord ID only, no campaign)
    # The frontend will use this to hit /campaigns/mine or /campaigns/join

    # We construct a special token payload
    # sub = discord_id (instead of username, because username is not unique globally across campaigns in our DB, but discord_id is unique to the human)
    # type = "global"

    token_payload = {
        "sub": discord_id,
        "type": "global",
        "username": username,
        "avatar": avatar,
        "discord_access_token": access_token # Store this temporarily if needed for fetching guilds later? Or client sends it?
        # Better to not store access_token in JWT. Client can keep it or we just re-ask for it?
        # Actually, we need the access_token to fetch guilds for "Joinable".
        # Let's return it in the response body, not the JWT.
    }

    jwt_token = security.create_access_token(data=token_payload)

    # Redirect to frontend with token
    # In a real app, you might set a cookie or redirect to a page that grabs the token from query params
    frontend_url = f"http://localhost:5173/login/callback?token={jwt_token}&discord_token={access_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/me", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user
