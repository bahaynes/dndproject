from pydantic import BaseModel
from typing import Optional, List
import datetime
from ..characters.base_schema import CharacterBase
from ..common.enums import SessionStatus


class CharacterInGameSession(CharacterBase):
    """Minimal character fields shown on a session."""

    id: int
    owner_id: int

    class Config:
        from_attributes = True


class GameSessionBase(BaseModel):
    """Shared session attributes."""

    mission_id: str
    title: str
    session_date: datetime.datetime
    status: SessionStatus = SessionStatus.OPEN
    route_data: List[str] = []
    gm_notes: Optional[str] = None
    aar_summary: Optional[str] = None


class GameSessionCreate(GameSessionBase):
    """Payload for creating or updating a session."""

    pass


class GameSession(GameSessionBase):
    """Session response with players attached."""

    id: str
    players: List[CharacterInGameSession] = []

    class Config:
        from_attributes = True


class GameSessionWithPlayers(GameSession):
    """Explicit alias kept for compatibility."""

    pass


class SessionSignupRequest(BaseModel):
    """Request payload when a player signs a character up for a session."""

    character_id: int
