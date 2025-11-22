from pydantic import BaseModel
from typing import Optional, List
import datetime
from ..characters.base_schema import CharacterBase

class CharacterInGameSession(CharacterBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class GameSessionBase(BaseModel):
    name: str
    description: Optional[str] = None
    session_date: datetime.datetime
    status: str = "Scheduled"
    after_action_report: Optional[str] = None
    target_tile_id: Optional[int] = None

class GameSessionCreate(GameSessionBase):
    pass

class GameSession(GameSessionBase):
    id: int
    players: List[CharacterInGameSession] = []
    class Config:
        from_attributes = True

class GameSessionWithPlayers(GameSession):
    pass
