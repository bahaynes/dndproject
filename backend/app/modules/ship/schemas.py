from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class TownLocation(BaseModel):
    """A visitable district or landmark on the campaign's Town Map."""

    id: str
    name: str
    npc: Optional[str] = None
    role: Optional[str] = None
    description: str
    services: list[str] = Field(default_factory=list)
    rumor: Optional[str] = None
    x: int = 50
    y: int = 50
    link_path: Optional[str] = None


class ShipBase(BaseModel):
    name: str = "The Ship"
    level: int = 1
    essence: int = 0
    motd: Optional[str] = None
    town_locations: list[TownLocation] = Field(default_factory=list)

    @field_validator("town_locations", mode="before")
    @classmethod
    def _coerce_none_locations(cls, v):
        return [] if v is None else v


class ShipUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    essence: Optional[int] = None
    motd: Optional[str] = None
    town_locations: Optional[list[TownLocation]] = None


class ShipOut(ShipBase):
    id: int
    campaign_id: int
    status: str  # "nominal" | "low" | "critical"
    long_rest_cost: int
    next_threshold: Optional[int]
    essence_to_next_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class ShipAdjust(BaseModel):
    essence_delta: int = 0
    description: str
