from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ShipBase(BaseModel):
    name: str = "The Ship"
    level: int = 1
    essence: int = 0
    motd: Optional[str] = None


class ShipUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    essence: Optional[int] = None
    motd: Optional[str] = None


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
