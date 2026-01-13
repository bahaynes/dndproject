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
