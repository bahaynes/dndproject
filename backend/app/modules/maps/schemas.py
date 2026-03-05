from pydantic import BaseModel
from typing import Optional, List, Any
from ..missions.schemas import Mission

class HexBase(BaseModel):
    q: int
    r: int
    terrain: str = "plains"
    is_discovered: bool = False
    hex_state: str = "wilderness"
    controlling_faction: Optional[str] = None
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
    hex_state: Optional[str] = None  # Admin only
    controlling_faction: Optional[str] = None  # Admin only

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
