from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

VALID_FACTIONS = {"Kathedral", "Vastarei"}


class FactionReputationEventBase(BaseModel):
    delta: int
    description: str
    session_id: Optional[int] = None


class FactionReputationEventCreate(FactionReputationEventBase):
    pass


class FactionReputationEvent(FactionReputationEventBase):
    id: int
    reputation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FactionReputationBase(BaseModel):
    faction_name: str
    level: int = 0

    @field_validator("faction_name")
    @classmethod
    def faction_must_be_valid(cls, v: str) -> str:
        if v not in VALID_FACTIONS:
            raise ValueError(f"faction_name must be one of {VALID_FACTIONS}")
        return v

    @field_validator("level")
    @classmethod
    def level_in_range(cls, v: int) -> int:
        if not (-5 <= v <= 5):
            raise ValueError("level must be between -5 and 5")
        return v


class FactionReputation(FactionReputationBase):
    id: int
    campaign_id: int
    events: List[FactionReputationEvent] = []

    class Config:
        from_attributes = True


class ReputationAdjust(BaseModel):
    delta: int
    description: str
    session_id: Optional[int] = None
