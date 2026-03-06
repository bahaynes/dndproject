from pydantic import BaseModel, field_validator
from typing import Optional, List, Any, Literal
from ..missions.schemas import Mission

HexState = Literal["wilderness", "claimed_developed", "friendly", "contested", "awakened"]
ControllingFaction = Literal["Inheritors", "Kathedral", "Vastarei"]

class HexBase(BaseModel):
    q: int
    r: int
    terrain: str = "plains"
    is_discovered: bool = False
    hex_state: HexState = "wilderness"
    controlling_faction: Optional[ControllingFaction] = None
    linked_location_name: Optional[str] = None
    linked_mission_id: Optional[int] = None

class HexCreate(HexBase):
    pass

class HexUpdate(BaseModel):
    terrain: Optional[str] = None
    is_discovered: Optional[bool] = None
    linked_location_name: Optional[str] = None
    linked_mission_id: Optional[int] = None
    notes: Optional[str] = None  # DM only
    hex_state: Optional[HexState] = None  # Admin only
    controlling_faction: Optional[ControllingFaction] = None  # Admin only

class PlayerNoteCreate(BaseModel):
    text: str
    session_id: Optional[int] = None

class Hex(HexBase):
    id: int
    map_id: int
    notes: Optional[str] = None
    hours_to_cross: Optional[float] = None
    player_notes: List[Any] = []
    linked_mission: Optional[Mission] = None

    @field_validator('player_notes', mode='before')
    @classmethod
    def coerce_none_to_list(cls, v: Any) -> List[Any]:
        return v if v is not None else []

    class Config:
        from_attributes = True

class HexMapBase(BaseModel):
    name: str
    width: int = 20
    height: int = 20
    hex_size: int = 60
    default_terrain: str = "plains"

class HexMapCreate(HexMapBase):
    pass

class HexMap(HexMapBase):
    id: int
    campaign_id: int
    hexes: List[Hex] = []

    class Config:
        from_attributes = True
