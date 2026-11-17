from pydantic import BaseModel
from typing import List, Optional, Literal
from ..auth.schemas import User
from ..items.schemas import Item, StoreItem
from ..missions.schemas import Mission
from ..sessions.schemas import GameSession

class GameDataExport(BaseModel):
    users: List[User]
    items: List[Item]
    store_items: List[StoreItem]
    missions: List[Mission]
    game_sessions: List[GameSession]


class WorldHub(BaseModel):
    name: str
    motd: Optional[str] = None


class WorldFaction(BaseModel):
    faction_name: str
    level: int = 0
    color: Optional[str] = None
    description: Optional[str] = None


class WorldItem(BaseModel):
    name: str
    description: Optional[str] = None
    store_price: Optional[int] = None
    store_quantity: Optional[int] = None


class WorldMissionReward(BaseModel):
    gold: Optional[int] = None
    xp: Optional[int] = 0
    item_name: Optional[str] = None
    is_hidden: bool = False
    hint: Optional[str] = None


class WorldMission(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "Available"
    tier: Optional[str] = None
    region: Optional[str] = None
    cooldown_days: int = 7
    is_discoverable: bool = True
    is_retired: bool = False
    prerequisite_name: Optional[str] = None
    rewards: List[WorldMissionReward] = []


class WorldHex(BaseModel):
    q: int
    r: int
    terrain: str = "plains"
    is_discovered: bool = False
    hex_state: str = "wilderness"
    controlling_faction: Optional[str] = None
    linked_location_name: Optional[str] = None
    linked_mission_name: Optional[str] = None
    notes: Optional[str] = None


class WorldMap(BaseModel):
    name: str
    width: int = 20
    height: int = 20
    hex_size: int = 60
    default_terrain: str = "plains"
    hexes: List[WorldHex] = []


class WorldBundle(BaseModel):
    schema_version: int = 1
    world_name: str
    exported_at: Optional[str] = None
    hub: Optional[WorldHub] = None
    factions: List[WorldFaction] = []
    items: List[WorldItem] = []
    missions: List[WorldMission] = []
    maps: List[WorldMap] = []


class WorldImportRequest(BaseModel):
    bundle: WorldBundle
    mode: Literal["merge", "replace"] = "merge"


class WorldImportResult(BaseModel):
    world_name: str
    mode: str
    factions_created: int = 0
    factions_updated: int = 0
    items_created: int = 0
    items_updated: int = 0
    missions_created: int = 0
    missions_updated: int = 0
    maps_created: int = 0
    maps_updated: int = 0
    hexes_upserted: int = 0
