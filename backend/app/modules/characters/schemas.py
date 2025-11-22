from pydantic import BaseModel
from typing import Optional, List

# Import from other modules
from ..items.schemas import InventoryItem
from .base_schema import CharacterBase
from ..missions.schemas import Mission
from ..sessions.schemas import GameSession


class CharacterStatsBase(BaseModel):
    """Core progression and readiness fields that are persisted with the character."""

    xp: int = 0
    commendations: int = 0
    current_hp: int = 0
    short_rest_available: bool = True


class CharacterStatsCreate(CharacterStatsBase):
    """Payload used when creating or resetting character stats."""

    pass


class CharacterStats(CharacterStatsBase):
    """Stats payload returned to the client."""

    id: int
    character_id: int

    class Config:
        from_attributes = True


class CharacterCreate(CharacterBase):
    """Payload for creating or updating a character profile."""

    stats: Optional[CharacterStatsCreate] = None


class Character(CharacterBase):
    """Full character response including relationships."""

    id: int
    owner_id: int
    stats: Optional[CharacterStats] = None
    inventory: List[InventoryItem] = []
    missions: List[Mission] = []
    game_sessions: List[GameSession] = []

    class Config:
        from_attributes = True
