from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ...database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    # Removing unique constraint on name because multiple campaigns can have items with same name
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Scoping
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    campaign = relationship("Campaign", back_populates="items")

    inventory_items = relationship("InventoryItem", back_populates="item")
    store_listing = relationship("StoreItem", back_populates="item", uselist=False)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, default=1, nullable=False)

    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    character = relationship("Character", back_populates="inventory")
    item = relationship("Item", back_populates="inventory_items")


class StoreItem(Base):
    __tablename__ = "store_items"

    id = Column(Integer, primary_key=True, index=True)
    price = Column(Integer, nullable=False)
    # -1 for infinite quantity
    quantity_available = Column(Integer, default=-1, nullable=False)

    item_id = Column(Integer, ForeignKey("items.id"), unique=True)
    item = relationship("Item", back_populates="store_listing")
