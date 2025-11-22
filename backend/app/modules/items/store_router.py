from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.post("/items/", response_model=schemas.StoreItem, tags=["Store"], dependencies=[Depends(get_current_active_admin_user)])
def create_store_item(store_item: schemas.StoreItemCreate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=store_item.item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item to be listed not found")
    return crud.create_store_item(db=db, store_item=store_item)

@router.get("/items/", response_model=List[schemas.StoreItem], tags=["Store"])
def read_store_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    store_items = crud.get_store_items(db, skip=skip, limit=limit)
    return store_items

@router.post("/items/{store_item_id}/purchase", tags=["Store"])
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
