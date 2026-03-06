from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

# --- Adventure Structure Schemas ---

class SceneOutline(BaseModel):
    name: str
    type: Literal["exploration", "social", "combat", "puzzle", "boss"]
    description: str
    encounters: List[str] = []        # Encounter references or descriptions
    transitions: List[str] = []       # Possible next scenes

class Act(BaseModel):
    title: str
    summary: str
    scenes: List[SceneOutline]
    key_npcs: List[str]

class AdventureStructure(BaseModel):
    title: str
    hook: str
    acts: List[Act]
    climax: str = "" # Description of the climax
    resolution: str

# --- API Request/Response Schemas ---

class OneShotGenerateRequest(BaseModel):
    # Context
    mission_ids: List[int] = []
    hex_region: Optional[str] = None
    revelation_layer: Literal["early", "mid", "late"] = "early"

    # Parameters
    party_size: int = 4
    party_level: int = 3
    duration_hours: float = 4.0
    tone: str = "heroic"  # heroic, grimdark, comedic, etc.

    # Feature flags for phases
    generate_dungeon: bool = False
    generate_visuals: bool = False
    generate_npcs: bool = False
    generate_pregens: bool = False

class OneShotResponse(BaseModel):
    id: int
    campaign_id: int
    title: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class OneShotDetailResponse(OneShotResponse):
    summary: Optional[str]
    content: Optional[Dict[str, Any]]
    generation_params: Dict[str, Any]
