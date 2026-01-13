from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user, get_current_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.post("/", response_model=schemas.Item, tags=["Items"])
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    return crud.create_item(db=db, item=item, campaign_id=current_user.campaign_id)

@router.get("/", response_model=List[schemas.Item], tags=["Items"])
def read_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = crud.get_items(db, campaign_id=current_user.campaign_id, skip=skip, limit=limit)
    return items

@router.get("/{item_id}", response_model=schemas.Item, tags=["Items"])
def read_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if db_item.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Item not found")

    return db_item
