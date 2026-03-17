from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ShipBase(BaseModel):
    name: str = "The Ship"
    level: int = 1
    fuel: int = 100
    max_fuel: int = 100
    crystals: int = 0
    credits: int = 0
    motd: Optional[str] = None


class ShipUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    fuel: Optional[int] = None
    max_fuel: Optional[int] = None
    crystals: Optional[int] = None
    credits: Optional[int] = None
    motd: Optional[str] = None


class ShipOut(ShipBase):
    id: int
    campaign_id: int
    status: str  # "nominal" | "low_fuel" | "critical"
    created_at: datetime

    class Config:
        from_attributes = True


class ShipAdjust(BaseModel):
    fuel_delta: int = 0
    crystal_delta: int = 0
    credit_delta: int = 0
    description: str
