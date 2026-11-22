from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


def _validate_relative_link_path(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("link_path must be a string")
    stripped = v.strip()
    if not stripped:
        return None
    if (
        not stripped.startswith("/")
        or stripped.startswith("//")
        or any(ch in stripped for ch in ("\r", "\n", "\\"))
    ):
        raise ValueError("link_path must be a relative path starting with '/'")
    return stripped


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

    @field_validator("link_path", mode="before")
    @classmethod
    def _validate_link_path(cls, v: Optional[str]) -> Optional[str]:
        return _validate_relative_link_path(v)


class TownLocationOut(TownLocation):
    """Response variant of TownLocation that coerces legacy invalid link_path values to None."""

    @field_validator("link_path", mode="before")
    @classmethod
    def _validate_link_path(cls, v: Optional[str]) -> Optional[str]:
        try:
            return _validate_relative_link_path(v)
        except ValueError:
            return None


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
    town_locations: list[TownLocationOut] = Field(default_factory=list)
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
