from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_user, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.get("/", response_model=List[schemas.HexMap], tags=["Maps"])
def read_maps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    maps = crud.get_maps(db, campaign_id=current_user.campaign_id)
    if not maps:
        # Lazy creation for existing campaigns
        default_map = schemas.HexMapCreate(
            name="The Known World",
            width=20,
            height=20,
            hex_size=60
        )
        new_map = crud.create_map(db, default_map, campaign_id=current_user.campaign_id, seed=True)
        return [new_map]
    return maps

@router.post("/", response_model=schemas.HexMap, tags=["Admin"])
def create_map(
    map_in: schemas.HexMapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    return crud.create_map(db, map_in, campaign_id=current_user.campaign_id)

@router.get("/{map_id}", response_model=schemas.HexMap, tags=["Maps"])
def read_map(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")

    return db_map

@router.put("/{map_id}/hexes/{q}/{r}", response_model=schemas.Hex, tags=["Admin"])
def update_hex(
    map_id: int,
    q: int,
    r: int,
    hex_update: schemas.HexUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")

    return crud.update_hex(db, map_id=map_id, q=q, r=r, hex_update=hex_update)
