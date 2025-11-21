from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user
from ..auth.schemas import User
from ..characters import service as char_service
from . import schemas, service as crud

# We might need two routers if we want different prefixes, or use one router with different tags/paths.
# Since main.py mounted everything on app, I will try to group them or use explicit paths.
# If I use router prefix in main.py, I can split this.
# But here I have /items, /inventory, /store.
# I will use one router and explicit paths relative to where it is mounted.
# If I mount this router at /api, then paths are /items, etc.

router = APIRouter()

# --- Item Endpoints ---
@router.post("/items/", response_model=schemas.Item, tags=["Items"], dependencies=[Depends(get_current_active_admin_user)])
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db=db, item=item)

@router.get("/items/", response_model=List[schemas.Item], tags=["Items"])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@router.get("/items/{item_id}", response_model=schemas.Item, tags=["Items"])
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# --- Inventory Endpoints ---
@router.post("/characters/{character_id}/inventory", response_model=schemas.InventoryItem, tags=["Inventory"], dependencies=[Depends(get_current_active_admin_user)])
def add_item_to_character_inventory(character_id: int, item_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    db_character = char_service.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.add_item_to_inventory(db=db, character_id=character_id, item_id=item_id, quantity=quantity)

@router.delete("/inventory/{inventory_item_id}", tags=["Inventory"])
def remove_item_from_character_inventory(
    inventory_item_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Logic from main.py
    removed_item = crud.remove_item_from_inventory(db, inventory_item_id=inventory_item_id, quantity=quantity)
    if removed_item is None:
        return {"detail": "Item removed from inventory or not found."}
    return removed_item


# --- Store Endpoints ---
@router.post("/store/items/", response_model=schemas.StoreItem, tags=["Store"], dependencies=[Depends(get_current_active_admin_user)])
def create_store_item(store_item: schemas.StoreItemCreate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=store_item.item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item to be listed not found")
    return crud.create_store_item(db=db, store_item=store_item)

@router.get("/store/items/", response_model=List[schemas.StoreItem], tags=["Store"])
def read_store_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    store_items = crud.get_store_items(db, skip=skip, limit=limit)
    return store_items

@router.post("/store/items/{store_item_id}/purchase", tags=["Store"])
def purchase_store_item(
    store_item_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    store_item = crud.get_store_item(db, store_item_id=store_item_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Store item not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character to purchase items for")

    result = crud.purchase_item(db, character=character, store_item=store_item, quantity=quantity)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
