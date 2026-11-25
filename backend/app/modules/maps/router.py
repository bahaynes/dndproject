from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List, Literal
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_admin_user, get_current_active_user
from ..auth.schemas import User
from . import schemas, service as crud
from .earth_baker import bake_earth_region, compute_bbox_from_center
from .storage import get_layer_storage

router = APIRouter()


def _redact_hex_for_user(hex_out: schemas.Hex, is_admin: bool) -> schemas.Hex:
    """Strip DM-only notes and hidden/retired linked missions for non-admin users."""
    if not is_admin:
        hex_out.notes = None
        if hex_out.linked_mission and (
            hex_out.linked_mission.is_retired or not hex_out.linked_mission.is_discoverable
        ):
            hex_out.linked_mission = None
            hex_out.linked_mission_id = None
    return hex_out


def _serialize_map_for_user(db_map, is_admin: bool) -> schemas.HexMap:
    """Serialize HexMap to schema and apply non-admin redaction."""
    map_out = schemas.HexMap.model_validate(db_map)
    if not is_admin:
        for hex_out in map_out.hexes:
            _redact_hex_for_user(hex_out, is_admin=False)
    return map_out


@router.get("/", response_model=List[schemas.HexMap], tags=["Maps"])
def read_maps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    is_admin = current_user.role == "admin"
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
        return [_serialize_map_for_user(new_map, is_admin=is_admin)]
    return [_serialize_map_for_user(m, is_admin=is_admin) for m in maps]

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
    current_user: User = Depends(get_current_active_user)
):
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")
        
    return _serialize_map_for_user(db_map, is_admin=(current_user.role == "admin"))

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

    if hex_update.linked_mission_id is not None:
        from ..missions import models as mission_models
        db_mission = (
            db.query(mission_models.Mission)
            .filter(
                mission_models.Mission.id == hex_update.linked_mission_id,
                mission_models.Mission.campaign_id == current_user.campaign_id,
            )
            .first()
        )
        if not db_mission:
            raise HTTPException(status_code=404, detail="Mission not found")

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
    return _redact_hex_for_user(
        schemas.Hex.model_validate(db_hex),
        is_admin=(current_user.role == "admin"),
    )


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

    hex_coords = [(h.q, h.r) for h in db_map.hexes]
    hex_size = db_map.hex_size or 60
    if payload.center_lat is not None and payload.center_lon is not None:
        min_lat, min_lon, max_lat, max_lon = compute_bbox_from_center(
            center_lat=payload.center_lat,
            center_lon=payload.center_lon,
            hex_coords=hex_coords,
            hex_size=hex_size,
            travel_scale=payload.travel_scale,
        )
    else:
        min_lat = payload.min_lat  # type: ignore[assignment]
        min_lon = payload.min_lon  # type: ignore[assignment]
        max_lat = payload.max_lat  # type: ignore[assignment]
        max_lon = payload.max_lon  # type: ignore[assignment]
        if max_lat <= min_lat or max_lon <= min_lon:
            raise HTTPException(status_code=400, detail="max_lat/max_lon must be greater than min_lat/min_lon")

    storage = get_layer_storage()
    try:
        result = await bake_earth_region(
            min_lat=min_lat,
            min_lon=min_lon,
            max_lat=max_lat,
            max_lon=max_lon,
            hex_coords=hex_coords,
            hex_size=hex_size,
            cache=storage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to bake Earth region: {exc}") from exc

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
        "center_lat": payload.center_lat if payload.center_lat is not None else round((min_lat + max_lat) / 2.0, 5),
        "center_lon": payload.center_lon if payload.center_lon is not None else round((min_lon + max_lon) / 2.0, 5),
        "travel_scale": payload.travel_scale,
        "min_lat": min_lat,
        "min_lon": min_lon,
        "max_lat": max_lat,
        "max_lon": max_lon,
        "zoom": result.zoom,
    }

    if payload.auto_seed_terrain:
        for h in db_map.hexes:
            new_terrain = result.hex_terrains.get((h.q, h.r))
            if new_terrain:
                h.terrain = new_terrain

    db.commit()
    db.refresh(db_map)
    db_map.bake_warnings = result.warnings  # response only, not a column
    return db_map


@router.get("/{map_id}/layers/{layer_type}", tags=["Maps"])
def get_map_layer_image(
    map_id: int,
    layer_type: Literal["topo", "satellite"],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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


@router.put("/{map_id}/routes", response_model=schemas.HexMap, tags=["Admin"])
def update_map_routes(
    map_id: int,
    payload: schemas.MapRoutesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    """Replace the road, trail, river, and sea-lane routes on a HexMap."""
    db_map = crud.get_map(db, map_id=map_id)
    if not db_map or db_map.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Map not found")

    db_map.routes = [r.model_dump() for r in payload.routes]
    db.commit()
    db.refresh(db_map)
    return db_map
