from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user, get_current_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.post("/items/", response_model=schemas.StoreItem, tags=["Store"])
def create_store_item(
    store_item: schemas.StoreItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    # Verify the underlying item belongs to the campaign
    item = crud.get_item(db, store_item.item_id)
    if not item or item.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=400, detail="Item not found or does not belong to this campaign")

    return crud.create_store_item(db=db, store_item=store_item)

@router.get("/items/", response_model=List[schemas.StoreItem], tags=["Store"])
def read_store_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    store_items = crud.get_store_items_by_campaign(db, campaign_id=current_user.campaign_id, skip=skip, limit=limit)
    return store_items

@router.get("/items/{store_item_id}", response_model=schemas.StoreItem, tags=["Store"])
def read_store_item(
    store_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_store_item = crud.get_store_item(db, store_item_id=store_item_id)
    if db_store_item is None:
        raise HTTPException(status_code=404, detail="Store item not found")

    if db_store_item.item.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Store item not found")

    return db_store_item

@router.post("/items/{store_item_id}/purchase", tags=["Store"])
def purchase_store_item(
    store_item_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_store_item = crud.get_store_item(db, store_item_id=store_item_id)
    if db_store_item is None:
        raise HTTPException(status_code=404, detail="Store item not found")

    if db_store_item.item.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Store item not found")

    result = crud.purchase_item(db, current_user.character, db_store_item, quantity)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
