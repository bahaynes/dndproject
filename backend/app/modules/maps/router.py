from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List, Literal
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_user, get_current_active_admin_user, get_current_active_user
from ..auth.schemas import User
from . import schemas, service as crud
from .earth_baker import bake_earth_region
from .storage import get_layer_storage

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

@router.post("/{map_id}/hexes/{q}/{r}/notes", response_model=schemas.Hex, tags=["Maps"])
def add_hex_note(
    map_id: int,
    q: int,
    r: int,
    note: schemas.PlayerNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")

    character = current_user.active_character
    if not character:
        raise HTTPException(status_code=400, detail="User has no active character selected")

    db_hex, error = crud.add_player_note(
        db,
        map_id=map_id,
        q=q,
        r=r,
        character_id=character.id,
        text=note.text,
        session_id=note.session_id
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return db_hex


@router.post("/{map_id}/bake-earth", response_model=schemas.HexMap, tags=["Admin"])
async def bake_earth_layers(
    map_id: int,
    payload: schemas.BakeEarthRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    """Bake Topographical and Satellite layers from real-Earth DEM + OSM natural features."""
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")
    if payload.max_lat <= payload.min_lat or payload.max_lon <= payload.min_lon:
        raise HTTPException(status_code=400, detail="max_lat/max_lon must be greater than min_lat/min_lon")

    hex_coords = [(h.q, h.r) for h in db_map.hexes]
    try:
        result = await bake_earth_region(
            min_lat=payload.min_lat,
            min_lon=payload.min_lon,
            max_lat=payload.max_lat,
            max_lon=payload.max_lon,
            hex_coords=hex_coords,
            hex_size=db_map.hex_size or 60,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to bake Earth region: {exc}") from exc

    storage = get_layer_storage()
    topo_key = storage.put_bytes(
        f"campaigns/{db_map.campaign_id}/maps/{db_map.id}/topo.png",
        result.topo_png,
        content_type="image/png",
    )
    sat_key = storage.put_bytes(
        f"campaigns/{db_map.campaign_id}/maps/{db_map.id}/satellite.png",
        result.satellite_png,
        content_type="image/png",
    )

    db_map.topo_image_key = topo_key
    db_map.satellite_image_key = sat_key
    db_map.layer_bounds = result.layer_bounds
    db_map.source_region = {
        "min_lat": payload.min_lat,
        "min_lon": payload.min_lon,
        "max_lat": payload.max_lat,
        "max_lon": payload.max_lon,
        "zoom": result.zoom,
    }

    if payload.auto_seed_terrain:
        for h in db_map.hexes:
            new_terrain = result.hex_terrains.get((h.q, h.r))
            if new_terrain:
                h.terrain = new_terrain

    db.commit()
    db.refresh(db_map)
    return db_map


@router.get("/{map_id}/layers/{layer_type}", tags=["Maps"])
def get_map_layer_image(
    map_id: int,
    layer_type: Literal["topo", "satellite"],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve the baked Topographical or Satellite PNG layer for a campaign map."""
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")

    key = db_map.topo_image_key if layer_type == "topo" else db_map.satellite_image_key
    if not key:
        raise HTTPException(status_code=404, detail="Map layer not found")

    data = get_layer_storage().get_bytes(key)
    if data is None:
        raise HTTPException(status_code=404, detail="Map layer asset missing")

    return Response(
        content=data,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )
