import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Set
import httpx
import logging

from ...database import get_db
from ...config import get_settings
from ... import security
from ...dependencies import get_current_user_global

from . import schemas, service as crud
from ..auth import service as auth_crud
from ..auth import schemas as auth_schemas

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.get("/bot-invite-url", tags=["Campaigns"])
async def get_bot_invite_url():
    """
    Returns the Discord bot invite URL constructed from DISCORD_CLIENT_ID.
    """
    client_id = getattr(settings, "DISCORD_CLIENT_ID", "")
    if not isinstance(client_id, str) or not client_id.strip():
        raise HTTPException(status_code=503, detail="Discord client ID is not configured.")
    return {
        "url": f"https://discord.com/oauth2/authorize?client_id={client_id.strip()}&scope=bot&permissions=0"
    }

@router.get("/mine", response_model=List[schemas.Campaign], tags=["Campaigns"])
async def get_my_campaigns(
    current_user_payload: dict = Depends(get_current_user_global),
    db: Session = Depends(get_db)
):
    """
    Returns a list of campaigns the user has joined (has a User record for).
    """
    discord_id = current_user_payload.get("sub")

    # Efficiently query for campaigns by joining User and Campaign tables
    from ..auth import models as auth_models
    from . import models as campaign_models

    campaigns = db.query(campaign_models.Campaign).join(auth_models.User).filter(auth_models.User.discord_id == discord_id).all()

    return campaigns

@router.post("/login", tags=["Campaigns"])
async def login_to_campaign(
    login_data: schemas.CampaignLogin,
    current_user_payload: dict = Depends(get_current_user_global),
    db: Session = Depends(get_db)
):
    """
    Exchanges a Global Token + Campaign ID for a Campaign Scoped Token.
    Verifies the user actually belongs to this campaign.
    """
    discord_id = current_user_payload.get("sub")

    user = auth_crud.get_user_by_discord_id(db, discord_id=discord_id, campaign_id=login_data.campaign_id)

    if not user:
        raise HTTPException(status_code=403, detail="You are not a member of this campaign.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account in this campaign is inactive.")

    # Create Campaign Scoped Token
    access_token = security.create_access_token(data={
        "sub": discord_id,
        "campaign_id": user.campaign_id,
        "role": user.role
    })

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/available", tags=["Campaigns"])
async def get_available_campaigns(
    discord_token: str = Body(..., embed=True),
    current_user_payload: dict = Depends(get_current_user_global),
    db: Session = Depends(get_db)
):
    """
    Lists campaigns that exist in the DB which the user is a member of on Discord,
    BUT has not joined in the app yet.
    Requires the client to pass the `discord_token` received during login.
    """
    # 1. Fetch user's guilds from Discord
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {discord_token}"}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch guilds from Discord")

    user_guilds = response.json()
    user_guild_ids = [g["id"] for g in user_guilds]

    # 2. Get campaigns from DB that match the user's guilds
    potential_campaigns = crud.get_campaigns_by_guild_ids(db, user_guild_ids)

    # 3. Filter out campaigns the user has already joined
    discord_id = current_user_payload.get("sub")
    from ..auth import models as auth_models
    existing_memberships = db.query(auth_models.User).filter(auth_models.User.discord_id == discord_id).all()
    joined_campaign_ids = {u.campaign_id for u in existing_memberships}

    available = [c for c in potential_campaigns if c.id not in joined_campaign_ids]

    return [schemas.Campaign.model_validate(c) for c in available]

def _get_admin_role_names() -> Set[str]:
    raw = getattr(settings, "ADMIN_DISCORD_ROLE_NAMES", "GM,DM")
    if not isinstance(raw, str):
        return set()
    return {name.strip().lower() for name in raw.split(",") if name.strip()}


async def _roles_contain_admin_name(
    client: httpx.AsyncClient,
    guild_id: str,
    member_role_ids: List[str],
    bot_token: str,
    admin_role_names: Set[str],
) -> bool:
    if not member_role_ids or not bot_token or not admin_role_names:
        return False
    roles_res = await client.get(
        f"https://discord.com/api/guilds/{guild_id}/roles",
        headers={"Authorization": f"Bot {bot_token}"},
    )
    if roles_res.status_code != 200:
        return False
    member_role_set = set(member_role_ids)
    for role in roles_res.json():
        if role.get("id") in member_role_set and role.get("name", "").strip().lower() in admin_role_names:
            return True
    return False


async def _user_has_admin_discord_role(
    client: httpx.AsyncClient,
    guild_id: str,
    discord_id: str,
    bot_token: str,
    admin_role_names: Set[str],
) -> bool:
    member_res = await client.get(
        f"https://discord.com/api/guilds/{guild_id}/members/{discord_id}",
        headers={"Authorization": f"Bot {bot_token}"},
    )
    if member_res.status_code != 200:
        return False
    member_roles = member_res.json().get("roles", [])
    return await _roles_contain_admin_name(client, guild_id, member_roles, bot_token, admin_role_names)


@router.post("/join", tags=["Campaigns"])
async def join_campaign(
    join_data: schemas.CampaignJoin,
    current_user_payload: dict = Depends(get_current_user_global),
    db: Session = Depends(get_db)
):
    """
    Joins a campaign if the user has the required roles on Discord.
    """
    discord_id = current_user_payload.get("sub")
    username = current_user_payload.get("username")
    avatar = current_user_payload.get("avatar")

    campaign = crud.get_campaign_by_guild_id(db, guild_id=join_data.discord_guild_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Check Discord Membership and Roles
    async with httpx.AsyncClient() as client:
        # We need the user's member object from the guild
        # Note: We can only do this if the BOT is in the guild.
        # We use the BOT TOKEN here, not the user's token.
        member_response = await client.get(
            f"https://discord.com/api/guilds/{campaign.discord_guild_id}/members/{discord_id}",
            headers={"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}
        )

        if member_response.status_code == 404:
            raise HTTPException(status_code=403, detail="You are not a member of this Discord server.")
        elif member_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to verify guild membership.")

        member_data = member_response.json()
        roles = member_data.get("roles", [])

        # Determine App Role
        app_role = None
        if campaign.dm_role_id and campaign.dm_role_id in roles:
            app_role = "admin"
        elif not campaign.dm_role_id:
            bot_token = getattr(settings, "DISCORD_BOT_TOKEN", "")
            if isinstance(bot_token, str) and bot_token.strip():
                if await _roles_contain_admin_name(
                    client,
                    campaign.discord_guild_id,
                    roles,
                    bot_token,
                    _get_admin_role_names(),
                ):
                    app_role = "admin"

        if app_role is None and campaign.player_role_id and campaign.player_role_id in roles:
            app_role = "player"

    # If no specific roles set, maybe allow anyone?
    # The requirement said: "if it matches an established dm server we check their roles if they are a player or a dm."
    # Implies we ONLY allow if they match.
    if not app_role:
         raise HTTPException(status_code=403, detail="You do not have the required Player or DM role in this server.")

    # Create or reactivate/sync existing User Record
    existing_user = auth_crud.get_user_by_discord_id(
        db, discord_id=discord_id, campaign_id=campaign.id
    )
    if existing_user:
        if not existing_user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Your account in this campaign is inactive.",
            )
        existing_user.role = app_role
        db.commit()
    else:
        user_create = auth_schemas.UserCreate(
            username=username,
            discord_id=discord_id,
            avatar_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png" if avatar else None,
            campaign_id=campaign.id,
            role=app_role
        )
        auth_crud.create_user(db, user_create)

    # Generate Token
    access_token = security.create_access_token(data={
        "sub": discord_id,
        "campaign_id": campaign.id,
        "role": app_role
    })

    return {"access_token": access_token, "token_type": "bearer", "campaign": schemas.Campaign.model_validate(campaign)}

@router.post("/setup", tags=["Admin"])
async def setup_campaign(
    setup_data: schemas.CampaignCreate,
    current_user_payload: dict = Depends(get_current_user_global),
    db: Session = Depends(get_db)
):
    """
    Initializes a new campaign for a Discord Guild.
    Restricted to ADMIN_DISCORD_IDS.
    """
    discord_id = current_user_payload.get("sub")
    allowed_admins = [admin_id.strip() for admin_id in settings.ADMIN_DISCORD_IDS.split(",") if admin_id.strip()]
    if discord_id not in allowed_admins:
        logger.warning(f"Unauthorized setup attempt by discord_id: {discord_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to setup campaigns.")

    # Check if already exists
    if crud.get_campaign_by_guild_id(db, setup_data.discord_guild_id):
        raise HTTPException(status_code=400, detail="Campaign already exists for this guild.")

    # Create campaign
    campaign = crud.create_campaign(db, setup_data)

    # Auto-assign the creator as the Admin of this campaign
    user_create = auth_schemas.UserCreate(
        username=current_user_payload.get("username"),
        discord_id=discord_id,
        avatar_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{current_user_payload.get('avatar')}.png" if current_user_payload.get("avatar") else None,
        campaign_id=campaign.id,
        role="admin"
    )
    new_user = auth_crud.create_user(db, user_create)

    # Generate Campaign Scoped Token (so they can go straight to dashboard)
    access_token = security.create_access_token(data={
        "sub": discord_id,
        "campaign_id": campaign.id,
        "role": "admin"
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "campaign": schemas.Campaign.model_validate(campaign),
        "user": auth_schemas.User.model_validate(new_user)
    }

@router.post("/discord/guilds", tags=["Admin"])
async def get_admin_discord_guilds(
    discord_token: str = Body(..., embed=True),
    current_user_payload: dict = Depends(get_current_user_global)
):
    """
    Lists guilds where the user has 'Manage Guild' (0x20), 'Administrator' (0x8),
    or a configured GM/DM role (checked via DISCORD_BOT_TOKEN).
    Used for the Setup page.
    """
    discord_id = current_user_payload.get("sub")
    allowed_admins = [admin_id.strip() for admin_id in settings.ADMIN_DISCORD_IDS.split(",") if admin_id.strip()]
    if discord_id not in allowed_admins:
        logger.warning(f"Unauthorized admin guilds view attempt by discord_id: {discord_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to view admin guilds.")

    bot_token = getattr(settings, "DISCORD_BOT_TOKEN", "")
    has_bot_token = isinstance(bot_token, str) and bool(bot_token.strip())
    admin_role_names = _get_admin_role_names()

    async with httpx.AsyncClient() as client:
        # Use httpx to make Discord API calls
        response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {discord_token}"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch guilds.")

        guilds = response.json()

        # Filter for Manage Guild (0x20) or Administrator (0x8) permission
        admin_guilds = []
        remaining_guilds = []
        for g in guilds:
            perms = int(g.get("permissions", "0"))
            if (perms & 0x20) == 0x20 or (perms & 0x8) == 0x8:
                admin_guilds.append(g)
            else:
                remaining_guilds.append(g)

        # Also include guilds where the user holds a GM/DM role (when the bot is in the guild)
        if remaining_guilds and has_bot_token and admin_role_names:
            sem = asyncio.Semaphore(10)

            async def _check_guild(g: dict) -> bool:
                async with sem:
                    return await _user_has_admin_discord_role(
                        client, g["id"], discord_id, bot_token, admin_role_names
                    )

            matches = await asyncio.gather(*[_check_guild(g) for g in remaining_guilds])
            for g, is_match in zip(remaining_guilds, matches):
                if is_match:
                    admin_guilds.append(g)

    return admin_guilds
