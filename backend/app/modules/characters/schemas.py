from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime

# Import from other modules
from ..items.schemas import InventoryItem
from .base_schema import CharacterBase, validate_http_url
from ..missions.schemas import Mission
from ..sessions.schemas import GameSession

class CharacterStatsBase(BaseModel):
    gold: int = 0
    xp: int = 0

class CharacterStatsCreate(CharacterStatsBase):
    pass

class CharacterStats(CharacterStatsBase):
    id: int
    character_id: int
    next_level_xp: Optional[int] = None
    class Config:
        from_attributes = True

class CharacterCreate(CharacterBase):
    level: int = Field(default=1, ge=1, le=20)

    @field_validator("character_sheet_url", "image_url", mode="before")
    @classmethod
    def _validate_urls(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v)


class CharacterUpdate(BaseModel):
    """Partial character update payload.

    Omitted fields remain unchanged; nullable fields (such as description,
    class_name, image_url, and character_sheet_url) can be cleared with null;
    non-nullable fields (name, level) reject explicit null; and only admins
    may modify level.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    character_sheet_url: Optional[str] = None
    class_name: Optional[str] = None
    level: Optional[int] = Field(default=None, ge=1, le=20)

    @field_validator("character_sheet_url", "image_url", mode="before")
    @classmethod
    def _validate_urls(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v)

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> "CharacterUpdate":
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        if "level" in self.model_fields_set and self.level is None:
            raise ValueError("level cannot be null")
        return self


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

    @field_validator("character_sheet_url", "image_url", mode="before")
    @classmethod
    def _coerce_legacy_unsafe_urls(cls, v: Optional[str]) -> Optional[str]:
        try:
            return validate_http_url(v)
        except ValueError:
            return None

    class Config:
        from_attributes = True


class CharacterStatusUpdate(BaseModel):
    status: str  # Active | Dead | Benched


class CharacterRosterEntry(BaseModel):
    """Lightweight character info for the party roster."""
    id: int
    name: str
    class_name: Optional[str] = None
    level: int
    xp: int = 0
    status: str
    date_of_death: Optional[datetime] = None
    missions_completed: int
    owner_id: int
    owner_username: Optional[str] = None

    class Config:
        from_attributes = True
