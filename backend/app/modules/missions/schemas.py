from pydantic import BaseModel
from typing import Optional, List
import datetime
from ..items.schemas import Item
from ..characters.base_schema import CharacterBase

# Schema for Character inside Mission response to avoid circular recursion
class CharacterInMission(CharacterBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

# Mission Schemas
class MissionRewardBase(BaseModel):
    item_id: Optional[int] = None
    xp: Optional[int] = None
    scrip: Optional[int] = None

class MissionRewardCreate(MissionRewardBase):
    pass

class MissionReward(MissionRewardBase):
    id: int
    item: Optional[Item] = None
    class Config:
        from_attributes = True

class MissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "Available"
    tier: Optional[str] = None
    region: Optional[str] = None
    last_run_date: Optional[datetime.datetime] = None
    cooldown_days: int = 7
    is_retired: bool = False
    is_discoverable: bool = True
    prerequisite_id: Optional[int] = None

class MissionCreate(MissionBase):
    rewards: List[MissionRewardCreate] = []

class Mission(MissionBase):
    id: int
    campaign_id: int
    rewards: List[MissionReward] = []
    players: List[CharacterInMission] = []
    class Config:
        from_attributes = True
