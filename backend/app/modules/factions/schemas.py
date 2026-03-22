from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


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
    color: Optional[str] = None
    description: Optional[str] = None

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


class FactionCreate(BaseModel):
    faction_name: str
    color: Optional[str] = None
    description: Optional[str] = None


class ReputationAdjust(BaseModel):
    delta: int
    description: str
    session_id: Optional[int] = None
