from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
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


RouteType = Literal["road", "trail", "sea_lane", "river"]


class RouteCoord(BaseModel):
    q: int
    r: int


class MapRoute(BaseModel):
    id: str
    name: str = ""
    type: RouteType = "road"
    hexes: List[RouteCoord] = []


class MapRoutesUpdate(BaseModel):
    routes: List[MapRoute]


TravelScale = Literal["local", "frontier", "expedition"]


class BakeEarthRequest(BaseModel):
    """Center pin + D&D travel scale (or explicit bbox) for baking a real-Earth region."""

    center_lat: Optional[float] = Field(default=None, ge=-84.0, le=84.0)
    center_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    travel_scale: TravelScale = "frontier"
    min_lat: Optional[float] = Field(default=None, ge=-85.0, le=85.0)
    min_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    max_lat: Optional[float] = Field(default=None, ge=-85.0, le=85.0)
    max_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    auto_seed_terrain: bool = True

    @model_validator(mode="after")
    def validate_location_inputs(self) -> "BakeEarthRequest":
        has_center = self.center_lat is not None and self.center_lon is not None
        has_bbox = all(v is not None for v in (self.min_lat, self.min_lon, self.max_lat, self.max_lon))
        if not has_center and not has_bbox:
            raise ValueError("Provide either center_lat/center_lon or min/max lat/lon bounds")
        return self


class HexMap(HexMapBase):
    id: int
    campaign_id: int
    topo_image_key: Optional[str] = Field(default=None, exclude=True)
    satellite_image_key: Optional[str] = Field(default=None, exclude=True)
    layer_bounds: Optional[LayerBounds] = None
    source_region: Optional[Dict[str, Any]] = None
    routes: List[MapRoute] = []
    hexes: List[Hex] = []

    @field_validator('routes', mode='before')
    @classmethod
    def coerce_none_routes_to_list(cls, v: Any) -> List[Any]:
        return v if v is not None else []

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
