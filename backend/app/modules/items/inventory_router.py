from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user
from ..auth.schemas import User
from ..characters import service as char_service
from . import schemas, service as crud

router = APIRouter()

@router.post("/", response_model=schemas.InventoryItem, tags=["Inventory"], dependencies=[Depends(get_current_active_admin_user)])
def add_item_to_character_inventory(character_id: int, item_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    db_character = char_service.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.add_item_to_inventory(db=db, character_id=character_id, item_id=item_id, quantity=quantity)

@router.delete("/{inventory_item_id}", tags=["Inventory"])
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
