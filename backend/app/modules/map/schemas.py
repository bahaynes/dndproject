from typing import List, Optional
from pydantic import BaseModel

from ..common.enums import HexOwnership, FogLevel
from ..common.dossier import Dossier


class TerrainDefBase(BaseModel):
    """Reusable attributes for terrain definitions."""

    name: str
    travel_cost_mult: float = 1.0
    color_hex: str
    icon_ref: Optional[str] = None


class TerrainDefCreate(TerrainDefBase):
    """Payload for creating or updating a terrain definition."""

    pass


class TerrainDef(TerrainDefBase):
    """Terrain definition response model."""

    id: str

    class Config:
        from_attributes = True


class HexDefBase(BaseModel):
    """Hex meta used on the map grid."""

    coordinate: str
    terrain_id: str
    owner: HexOwnership = HexOwnership.NEUTRAL
    fog_level: FogLevel = FogLevel.BLACK
    dossier_data: Optional[Dossier] = None


class HexDefCreate(HexDefBase):
    """Payload for creating or updating a hex."""

    pass


class HexDef(HexDefBase):
    """Hex response model."""

    class Config:
        from_attributes = True
