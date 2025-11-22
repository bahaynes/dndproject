from pydantic import BaseModel
from typing import Optional


class ItemBase(BaseModel):
    """Shared item fields."""

    name: str
    description: Optional[str] = None
    rarity: str = "common"
    attunement_required: bool = False


class ItemCreate(ItemBase):
    """Payload for creating or updating an item."""

    pass


class Item(ItemBase):
    """Item response model."""

    id: int

    class Config:
        from_attributes = True


class InventoryItemBase(BaseModel):
    """Inventory row stored per character."""

    quantity: int
    is_attuned: bool = False


class InventoryItemCreate(InventoryItemBase):
    """Payload when adding an item to inventory."""

    item_id: int


class InventoryItem(InventoryItemBase):
    """Inventory item response including item details."""

    id: int
    item: Item

    class Config:
        from_attributes = True


class StoreItemBase(BaseModel):
    """Store listing metadata."""

    price: int
    quantity_available: int


class StoreItemCreate(StoreItemBase):
    """Payload to create a store listing."""

    item_id: int


class StoreItem(StoreItemBase):
    """Store listing response."""

    id: int
    item: Item

    class Config:
        from_attributes = True
