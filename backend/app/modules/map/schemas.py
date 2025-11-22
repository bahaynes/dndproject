from pydantic import BaseModel
from typing import Optional

class MapTileBase(BaseModel):
    q: int
    r: int
    terrain: str
    description: Optional[str] = None

class MapTileCreate(MapTileBase):
    is_revealed: bool = False
    notes: Optional[str] = None

class MapTileUpdate(BaseModel):
    terrain: Optional[str] = None
    is_revealed: Optional[bool] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class MapTilePublic(MapTileBase):
    id: int
    is_revealed: bool

    class Config:
        from_attributes = True

class MapTileAdmin(MapTilePublic):
    notes: Optional[str] = None
