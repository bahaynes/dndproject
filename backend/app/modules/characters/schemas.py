from pydantic import BaseModel
from typing import Optional, List

# Import from other modules
from ..items.schemas import InventoryItem
from .base_schema import CharacterBase
from ..missions.schemas import Mission
from ..sessions.schemas import GameSession

class CharacterStatsBase(BaseModel):
    xp: int = 0
    scrip: int = 0

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
    stats: CharacterStats
    inventory: List[InventoryItem] = []
    missions: List[Mission] = []
    game_sessions: List[GameSession] = []

    class Config:
        from_attributes = True
