from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...dependencies import get_db, get_current_active_admin_user
from . import schemas, service

router = APIRouter(prefix="/api/map", tags=["Map"])


@router.get("/terrain", response_model=List[schemas.TerrainDef])
def list_terrain(db: Session = Depends(get_db)):
    """Return all terrain definitions for populating the hex map legend."""

    return service.list_terrain(db)


@router.post(
    "/terrain",
    response_model=schemas.TerrainDef,
    dependencies=[Depends(get_current_active_admin_user)],
    status_code=status.HTTP_201_CREATED,
)
def create_terrain(terrain: schemas.TerrainDefCreate, db: Session = Depends(get_db)):
    """Create a terrain definition (admin only)."""

    return service.create_terrain(db, terrain)


@router.put(
    "/terrain/{terrain_id}",
    response_model=schemas.TerrainDef,
    dependencies=[Depends(get_current_active_admin_user)],
)
def update_terrain(terrain_id: str, terrain: schemas.TerrainDefCreate, db: Session = Depends(get_db)):
    """Update a terrain definition (admin only)."""

    updated = service.update_terrain(db, terrain_id, terrain)
    if not updated:
        raise HTTPException(status_code=404, detail="Terrain not found")
    return updated


@router.get("/hexes", response_model=List[schemas.HexDef])
def list_hexes(db: Session = Depends(get_db)):
    """Return all hexes for rendering the campaign map."""

    return service.list_hexes(db)


@router.put(
    "/hexes/{coordinate}",
    response_model=schemas.HexDef,
    dependencies=[Depends(get_current_active_admin_user)],
)
def upsert_hex(coordinate: str, hex_in: schemas.HexDefCreate, db: Session = Depends(get_db)):
    """Create or update a hex (admin only)."""

    if coordinate != hex_in.coordinate:
        raise HTTPException(status_code=400, detail="Coordinate mismatch between path and payload")
    return service.upsert_hex(db, hex_in)
