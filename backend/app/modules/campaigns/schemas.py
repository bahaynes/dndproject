from pydantic import BaseModel
from typing import Optional, List

class CampaignBase(BaseModel):
    name: str
    discord_guild_id: str

class CampaignCreate(CampaignBase):
    dm_role_id: Optional[str] = None
    player_role_id: Optional[str] = None

class Campaign(CampaignBase):
    id: int
    dm_role_id: Optional[str]
    player_role_id: Optional[str]

    class Config:
        from_attributes = True

class CampaignJoin(BaseModel):
    discord_guild_id: str
    discord_access_token: str # Needed to verify membership via Discord API

class CampaignLogin(BaseModel):
    campaign_id: int


class CampaignRolesUpdate(BaseModel):
    dm_role_id: Optional[str] = None
    player_role_id: Optional[str] = None


class DiscordRoleOption(BaseModel):
    id: str
    name: str
    color: int = 0


class CampaignDiscordRolesResponse(BaseModel):
    roles: List[DiscordRoleOption]
    dm_role_id: Optional[str] = None
    player_role_id: Optional[str] = None
    bot_connected: bool = False
    warning: Optional[str] = None


class CampaignMemberOut(BaseModel):
    id: int
    username: str
    discord_id: str
    avatar_url: Optional[str] = None
    role: str
    is_active: bool = True

    class Config:
        from_attributes = True


class CampaignMemberRoleUpdate(BaseModel):
    role: str
