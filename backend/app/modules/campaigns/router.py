from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
import httpx

from ...database import get_db
from ...config import get_settings
from ... import security
from ...dependencies import get_current_user_global

from . import schemas, service as crud
from ..auth import service as auth_crud
from ..auth import schemas as auth_schemas

router = APIRouter()
settings = get_settings()

@router.get("/mine", response_model=List[schemas.Campaign], tags=["Campaigns"])
async def get_my_campaigns(
    current_user_payload: dict = Depends(get_current_user_global),
    db: Session = Depends(get_db)
):
    """
    Returns a list of campaigns the user has joined (has a User record for).
    """
    discord_id = current_user_payload.get("sub")

    # This query joins Users and Campaigns
    # Find all user records for this discord_id
    from ..auth import models as auth_models
    user_records = db.query(auth_models.User).filter(auth_models.User.discord_id == discord_id).all()

    campaigns = []
    for record in user_records:
        if record.campaign:
            campaigns.append(record.campaign)

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

    # 2. Get all active campaigns from DB
    all_campaigns = crud.get_all_campaigns(db)

    # 3. Filter: Campaign Must be in User's Guilds AND User must NOT be in Campaign DB
    discord_id = current_user_payload.get("sub")
    existing_memberships = db.query(auth_models.User).filter(auth_models.User.discord_id == discord_id).all()
    joined_campaign_ids = [u.campaign_id for u in existing_memberships]

    available = []
    for campaign in all_campaigns:
        if campaign.discord_guild_id in user_guild_ids and campaign.id not in joined_campaign_ids:
            available.append(campaign)

    return available

from ..auth import models as auth_models # Import here to avoid early import issues if any

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
    elif campaign.player_role_id and campaign.player_role_id in roles:
        app_role = "player"

    # If no specific roles set, maybe allow anyone?
    # The requirement said: "if it matches an established dm server we check their roles if they are a player or a dm."
    # Implies we ONLY allow if they match.
    if not app_role:
         raise HTTPException(status_code=403, detail="You do not have the required Player or DM role in this server.")

    # Create User Record
    user_create = auth_schemas.UserCreate(
        username=username,
        discord_id=discord_id,
        avatar_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png" if avatar else None,
        campaign_id=campaign.id,
        role=app_role
    )

    new_user = auth_crud.create_user(db, user_create)

    # Generate Token
    access_token = security.create_access_token(data={
        "sub": discord_id,
        "campaign_id": campaign.id,
        "role": app_role
    })

    return {"access_token": access_token, "token_type": "bearer", "campaign": campaign}

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
    allowed_admins = settings.ADMIN_DISCORD_IDS.split(",")
    if discord_id not in allowed_admins:
        raise HTTPException(status_code=403, detail="You are not authorized to setup campaigns.")

    # Check if already exists
    if crud.get_campaign_by_guild_id(db, setup_data.discord_guild_id):
        raise HTTPException(status_code=400, detail="Campaign already exists for this guild.")

    # Create
    campaign = crud.create_campaign(db, setup_data)

    return campaign

@router.post("/discord/guilds", tags=["Admin"])
async def get_admin_discord_guilds(
    discord_token: str = Body(..., embed=True),
    current_user_payload: dict = Depends(get_current_user_global)
):
    """
    Lists guilds where the user has 'Manage Guild' permissions.
    Used for the Setup page.
    """
    discord_id = current_user_payload.get("sub")
    allowed_admins = settings.ADMIN_DISCORD_IDS.split(",")
    if discord_id not in allowed_admins:
        raise HTTPException(status_code=403, detail="You are not authorized to view admin guilds.")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {discord_token}"}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch guilds.")

    guilds = response.json()

    # Filter for Manage Guild permission (0x20)
    # Permissions are a bit string.
    # We can simplified and just return all, or do the bitwise check.
    # Javascript handles bitwise fine, but let's do it here.
    # Permission integer is in "permissions" (string).

    admin_guilds = []
    for g in guilds:
        perms = int(g.get("permissions", "0"))
        if (perms & 0x20) == 0x20: # MANAGE_GUILD
            admin_guilds.append(g)

    return admin_guilds
