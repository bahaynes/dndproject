from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Import from other modules
from ..items.schemas import InventoryItem
from .base_schema import CharacterBase
from ..missions.schemas import Mission
from ..sessions.schemas import GameSession

class CharacterStatsBase(BaseModel):
    gold: int = 0

class CharacterStatsCreate(CharacterStatsBase):
    pass

class CharacterStats(CharacterStatsBase):
    id: int
    character_id: int
    class Config:
        from_attributes = True

class CharacterCreate(CharacterBase):
    pass

class Character(CharacterBase):
    id: int
    owner_id: int
    status: str = "Active"
    date_of_death: Optional[datetime] = None
    missions_completed: int = 0
    stats: CharacterStats
    inventory: List[InventoryItem] = []
    missions: List[Mission] = []
    game_sessions: List[GameSession] = []

    class Config:
        from_attributes = True


class CharacterStatusUpdate(BaseModel):
    status: str  # Active | Dead | Benched


class CharacterRosterEntry(BaseModel):
    """Lightweight character info for the crew roster."""
    id: int
    name: str
    class_name: Optional[str] = None
    level: int
    status: str
    date_of_death: Optional[datetime] = None
    missions_completed: int
    owner_id: int
    owner_username: Optional[str] = None

    class Config:
        from_attributes = True
