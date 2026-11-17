from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional, List, Any, Literal, Dict
from ..missions.schemas import Mission

HexState = Literal["wilderness", "claimed_developed", "friendly", "contested", "awakened"]

class HexBase(BaseModel):
    q: int
    r: int
    terrain: str = "plains"
    is_discovered: bool = False
    hex_state: HexState = "wilderness"
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
    hex_state: Optional[HexState] = None  # Admin only
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

class LayerBounds(BaseModel):
    min_x: float
    min_y: float
    max_x: float
    max_y: float


class BakeEarthRequest(BaseModel):
    """Bounding box and options for baking a real-Earth region onto a HexMap."""

    min_lat: float = Field(..., ge=-85.0, le=85.0)
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lat: float = Field(..., ge=-85.0, le=85.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)
    auto_seed_terrain: bool = True


class HexMap(HexMapBase):
    id: int
    campaign_id: int
    topo_image_key: Optional[str] = Field(default=None, exclude=True)
    satellite_image_key: Optional[str] = Field(default=None, exclude=True)
    layer_bounds: Optional[LayerBounds] = None
    source_region: Optional[Dict[str, Any]] = None
    hexes: List[Hex] = []

    @computed_field
    @property
    def topo_image_url(self) -> Optional[str]:
        if not self.topo_image_key:
            return None
        return f"/api/maps/{self.id}/layers/topo"

    @computed_field
    @property
    def satellite_image_url(self) -> Optional[str]:
        if not self.satellite_image_key:
            return None
        return f"/api/maps/{self.id}/layers/satellite"

    class Config:
        from_attributes = True
