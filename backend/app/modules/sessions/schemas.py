from pydantic import BaseModel, model_validator
from typing import Optional, List
import datetime
from ..characters.base_schema import CharacterBase
from ..missions.schemas import Mission

class CharacterInGameSession(CharacterBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class HexInSession(BaseModel):
    id: int
    q: int
    r: int
    terrain: str
    linked_location_name: Optional[str] = None
    class Config:
        from_attributes = True

class GameSessionBase(BaseModel):
    name: str
    description: Optional[str] = None
    session_date: datetime.datetime
    status: str = "Scheduled"
    after_action_report: Optional[str] = None
    field_report: Optional[str] = None
    min_players: int = 4
    max_players: int = 6
    confirmed_mission_id: Optional[int] = None
    confirmed_hex_id: Optional[int] = None

class GameSessionCreate(GameSessionBase):
    pass

class GameSession(GameSessionBase):
    id: int
    players: List[CharacterInGameSession] = []
    class Config:
        from_attributes = True

class FieldReportUpdate(BaseModel):
    field_report: str

class SwapCharacterRequest(BaseModel):
    character_id: int

class SessionCompleteRequest(BaseModel):
    result: str  # "success" | "failure"
    mission_id: Optional[int] = None
    hex_id: Optional[int] = None
    essence_earned: int = 0
    gold_earned: int = 0
    xp_earned: int = 0
    after_action_report: Optional[str] = None
    casualties: List[int] = []  # character IDs to mark as Dead

class SessionProposalBase(BaseModel):
    session_id: int
    mission_id: Optional[int] = None
    hex_id: Optional[int] = None

class SessionProposalCreate(SessionProposalBase):
    @model_validator(mode="after")
    def require_mission_or_hex(self):
        if self.mission_id is None and self.hex_id is None:
            raise ValueError("Either mission_id or hex_id must be provided")
        return self

class SessionProposal(SessionProposalBase):
    id: int
    proposed_by_id: int
    status: str
    mission: Optional[Mission] = None
    hex: Optional[HexInSession] = None
    backers: List[CharacterInGameSession] = []
    class Config:
        from_attributes = True

class GameSessionWithPlayers(GameSession):
    result: Optional[str] = None
    essence_earned: Optional[int] = None
    proposals: List[SessionProposal] = []
    confirmed_mission: Optional[Mission] = None
    confirmed_hex: Optional[HexInSession] = None
