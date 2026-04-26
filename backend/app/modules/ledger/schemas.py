from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

VALID_EVENT_TYPES = {
    "MissionCompleted",
    "MissionFailed",
    "CharacterDeath",
    "LevelUp",
    "Purchase",
    "RewardDistribution",
    "AdminAdjustment",
    "ShipAdjustment",
}


class LedgerEntryCreate(BaseModel):
    event_type: str
    description: str
    essence_delta: int = 0
    gold_delta: int = 0
    hp_delta: int = 0
    session_id: Optional[int] = None
    ship_snapshot: Optional[Dict[str, Any]] = None


class LedgerEntryOut(BaseModel):
    id: int
    campaign_id: int
    session_id: Optional[int] = None
    event_type: str
    description: str
    essence_delta: int
    gold_delta: int = 0
    hp_delta: int = 0
    ship_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
