from pydantic import BaseModel
from typing import Optional, List
import datetime
from ..characters.base_schema import CharacterBase
from ..missions.schemas import Mission

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
    min_players: int = 4
    max_players: int = 6
    confirmed_mission_id: Optional[int] = None

class GameSessionCreate(GameSessionBase):
    pass

class GameSession(GameSessionBase):
    id: int
    players: List[CharacterInGameSession] = []
    class Config:
        from_attributes = True

class SessionProposalBase(BaseModel):
    session_id: int
    mission_id: int

class SessionProposalCreate(SessionProposalBase):
    pass

class SessionProposal(SessionProposalBase):
    id: int
    proposed_by_id: int
    status: str
    mission: Mission
    backers: List[CharacterInGameSession] = []
    class Config:
        from_attributes = True

class GameSessionWithPlayers(GameSession):
    proposals: List[SessionProposal] = []
    confirmed_mission: Optional[Mission] = None
