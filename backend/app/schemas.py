from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime


# CharacterStats Schemas
class CharacterStatsBase(BaseModel):
    xp: int = 0
    scrip: int = 0

class CharacterStatsCreate(CharacterStatsBase):
    pass

class CharacterStats(CharacterStatsBase):
    id: int
    character_id: int

    class Config:
        from_attributes = True


# Item Schemas
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    class Config:
        from_attributes = True

# InventoryItem Schemas
class InventoryItemBase(BaseModel):
    quantity: int

class InventoryItemCreate(InventoryItemBase):
    item_id: int

class InventoryItem(InventoryItemBase):
    id: int
    item: Item
    class Config:
        from_attributes = True

# StoreItem Schemas
class StoreItemBase(BaseModel):
    price: int
    quantity_available: int

class StoreItemCreate(StoreItemBase):
    item_id: int

class StoreItem(StoreItemBase):
    id: int
    item: Item
    class Config:
        from_attributes = True


# Mission Schemas
class MissionRewardBase(BaseModel):
    item_id: Optional[int] = None
    xp: Optional[int] = None
    scrip: Optional[int] = None

class MissionRewardCreate(MissionRewardBase):
    pass

class MissionReward(MissionRewardBase):
    id: int
    item: Optional[Item] = None
    class Config:
        from_attributes = True

class MissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "Available"

class MissionCreate(MissionBase):
    rewards: List[MissionRewardCreate] = []

class Mission(MissionBase):
    id: int
    rewards: List[MissionReward] = []
    players: List['Character'] = []
    class Config:
        from_attributes = True


# GameSession Schemas
class GameSessionBase(BaseModel):
    name: str
    description: Optional[str] = None
    session_date: datetime.datetime
    status: str = "Scheduled"
    after_action_report: Optional[str] = None

class GameSessionCreate(GameSessionBase):
    pass

class GameSession(GameSessionBase):
    id: int
    players: List['Character'] = []
    class Config:
        from_attributes = True


# Character Schemas
class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class CharacterCreate(CharacterBase):
    pass


class Character(CharacterBase):
    id: int
    owner_id: int
    stats: CharacterStats
    inventory: List[InventoryItem] = []
    missions: List[Mission] = []
    game_sessions: List[GameSession] = []

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: str = "player"


class User(UserBase):
    id: int
    is_active: bool
    role: str
    character: Optional[Character] = None

    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Data Export/Import Schemas
class GameDataExport(BaseModel):
    users: List[User]
    # Characters are nested in Users
    items: List[Item]
    store_items: List[StoreItem]
    missions: List[Mission]
    game_sessions: List[GameSession]


# Resolve forward references for circular dependencies
Mission.model_rebuild()
GameSession.model_rebuild()
Character.model_rebuild()
