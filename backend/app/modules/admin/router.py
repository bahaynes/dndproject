from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import json

from ...dependencies import get_db, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.post("/seed", tags=["Admin"])
def seed_world_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    """Idempotent: seeds factions and opening missions from the world bible."""
    from scripts.seed import seed_factions, seed_missions
    factions = seed_factions(db, current_user.campaign_id)
    missions = seed_missions(db, current_user.campaign_id)
    db.commit()
    return {"factions_created": factions, "missions_created": missions}


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
