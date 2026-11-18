from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import json

from ...dependencies import get_db, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.get("/presets", response_model=list[schemas.WorldPresetSummary], tags=["Admin"])
def list_world_presets(
    current_user: User = Depends(get_current_active_admin_user),
):
    """List available built-in starter world presets."""
    return crud.list_world_presets()


@router.post("/seed", response_model=schemas.WorldImportResult, tags=["Admin"])
def seed_world_data(
    preset: str = "baseline_world",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    """Idempotent: seeds a built-in starter world preset (hub, factions, store, quests, optional hex map)."""
    try:
        bundle = crud.load_world_preset(preset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return crud.import_world(db, current_user.campaign_id, bundle, mode="merge")


@router.get("/world/export", response_model=schemas.WorldBundle, tags=["Admin"])
def export_world_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    return crud.export_world(db, current_user.campaign_id)


@router.post("/world/import", response_model=schemas.WorldImportResult, tags=["Admin"])
def import_world_endpoint(
    req: schemas.WorldImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    return crud.import_world(db, current_user.campaign_id, req.bundle, mode=req.mode)


@router.get("/export", response_model=schemas.GameDataExport, tags=["Admin"], dependencies=[Depends(get_current_active_admin_user)])
def export_data(db: Session = Depends(get_db)):
    return crud.export_game_data(db)

@router.post("/import", tags=["Admin"], dependencies=[Depends(get_current_active_admin_user)])
async def import_data(db: Session = Depends(get_db), file: UploadFile = File(...)):
    try:
        contents = await file.read()
        data = json.loads(contents)
        result = crud.import_game_data(db, data)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during import: {e}")
