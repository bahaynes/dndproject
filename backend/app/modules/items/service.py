from sqlalchemy.orm import Session
from . import models, schemas
from ..characters.models import Character

# Item CRUD
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Inventory CRUD
def add_item_to_inventory(db: Session, character_id: int, item_id: int, quantity: int = 1):
    # Check if the item already exists in the character's inventory
    db_inventory_item = db.query(models.InventoryItem).filter(
        models.InventoryItem.character_id == character_id,
        models.InventoryItem.item_id == item_id
    ).first()

    if db_inventory_item:
        db_inventory_item.quantity += quantity
    else:
        db_inventory_item = models.InventoryItem(
            character_id=character_id,
            item_id=item_id,
            quantity=quantity
        )
        db.add(db_inventory_item)

    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

def remove_item_from_inventory(db: Session, inventory_item_id: int, quantity: int = 1):
    db_inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == inventory_item_id).first()
    if not db_inventory_item:
        return None

    db_inventory_item.quantity -= quantity
    if db_inventory_item.quantity <= 0:
        db.delete(db_inventory_item)
        db.commit()
        return None # Item removed completely

    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

# Store CRUD
def get_store_item(db: Session, store_item_id: int):
    return db.query(models.StoreItem).filter(models.StoreItem.id == store_item_id).first()

def get_store_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.StoreItem).offset(skip).limit(limit).all()

def create_store_item(db: Session, store_item: schemas.StoreItemCreate):
    db_store_item = models.StoreItem(**store_item.model_dump())
    db.add(db_store_item)
    db.commit()
    db.refresh(db_store_item)
    return db_store_item

def purchase_item(db: Session, character: Character, store_item: models.StoreItem, quantity: int):
    if store_item.price * quantity > character.stats.scrip:
        return {"error": "Not enough scrip"}

    if store_item.quantity_available != -1 and store_item.quantity_available < quantity:
        return {"error": "Not enough items in stock"}

    # Deduct scrip
    character.stats.scrip -= store_item.price * quantity

    # Decrement store quantity if not infinite
    if store_item.quantity_available != -1:
        store_item.quantity_available -= quantity

    # Add item to character's inventory
    add_item_to_inventory(db, character_id=character.id, item_id=store_item.item_id, quantity=quantity)

    db.commit()
    return {"message": "Purchase successful"}
