from pydantic import BaseModel
from typing import Optional, List
from ..characters.base_schema import CharacterBase
from ..common.dossier import Dossier


class CharacterInMission(CharacterBase):
    """Minimal character data shown on mission planning views."""

    id: int
    owner_id: int

    class Config:
        from_attributes = True


class MissionBase(BaseModel):
    """Reusable attributes for a mission definition."""

    title: str
    summary: Optional[str] = None
    status: str = "available"
    target_hex: Optional[str] = None
    dossier_data: Optional[Dossier] = None


class MissionCreate(MissionBase):
    """Payload for creating or updating a mission."""

    pass


class Mission(MissionBase):
    """Mission response with roster information."""

    id: str
    players: List[CharacterInMission] = []

    class Config:
        from_attributes = True


class MissionWithPlayers(Mission):
    """Alias retained for backwards compatibility."""

    pass
