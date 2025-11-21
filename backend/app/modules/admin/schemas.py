from pydantic import BaseModel
from typing import List
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
