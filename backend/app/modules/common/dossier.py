"""Pydantic models that capture the shared dossier JSON structure for missions and hexes."""
from typing import List, Optional
from pydantic import BaseModel


class DossierMonster(BaseModel):
    """Monster reference for an encounter."""

    name: str
    url: Optional[str] = None
    cr: float
    count: int


class DossierLoot(BaseModel):
    """Loot definition keyed off Item IDs to keep the data normalized."""

    gold: int = 0
    items: List[int] = []


class DossierEncounter(BaseModel):
    """An encounter block a GM can run from the dossier."""

    id: str
    name: str
    type: str
    cr_estimate: Optional[float] = None
    description: Optional[str] = None
    monsters: List[DossierMonster] = []
    loot: Optional[DossierLoot] = None
    xp_reward: Optional[int] = None


class DossierCompletionReward(BaseModel):
    """Rewards granted when the mission is completed."""

    xp: int = 0
    gold: int = 0
    commendations: int = 0


class Dossier(BaseModel):
    """Aggregated dossier containing encounters and completion rewards."""

    gm_notes: Optional[str] = None
    encounters: List[DossierEncounter] = []
    completion_reward: Optional[DossierCompletionReward] = None
