from pydantic import BaseModel, Field
from typing import Optional

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
    quantity: int = Field(..., ge=1)

class InventoryItem(InventoryItemBase):
    id: int
    item: Item
    class Config:
        from_attributes = True

# StoreItem Schemas
class StoreItemBase(BaseModel):
    price: int = Field(..., ge=0)
    quantity_available: int = Field(..., ge=-1)

class StoreItemCreate(StoreItemBase):
    item_id: int

class StoreItem(StoreItemBase):
    id: int
    item: Item
    class Config:
        from_attributes = True
