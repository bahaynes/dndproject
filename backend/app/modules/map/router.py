from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...dependencies import get_db, get_current_active_user
from ..auth.schemas import User
from . import schemas, crud

router = APIRouter()

@router.get("/tiles", response_model=List[schemas.MapTilePublic])
def read_tiles(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    is_admin = current_user.role == "admin"
    revealed_only = not is_admin
    return crud.get_tiles(db, skip=skip, limit=limit, revealed_only=revealed_only)

@router.post("/tiles", response_model=schemas.MapTileAdmin)
def create_tile(
    tile: schemas.MapTileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")

    existing = crud.get_tile_by_coords(db, tile.q, tile.r)
    if existing:
        raise HTTPException(status_code=400, detail="Tile already exists at these coordinates")

    return crud.create_tile(db, tile)

@router.put("/tiles/{tile_id}", response_model=schemas.MapTileAdmin)
def update_tile(
    tile_id: int,
    tile_update: schemas.MapTileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")

    updated = crud.update_tile(db, tile_id, tile_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Tile not found")
    return updated
