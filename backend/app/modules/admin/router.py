from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import json

from ...dependencies import get_db, get_current_active_admin_user
from . import schemas, service as crud

router = APIRouter()

@router.get("/export", response_model=schemas.GameDataExport, tags=["Admin"], dependencies=[Depends(get_current_active_admin_user)])
def export_data(db: Session = Depends(get_db)):
    """Export core game data for backup."""

    return crud.export_game_data(db)

@router.post("/import", tags=["Admin"], dependencies=[Depends(get_current_active_admin_user)])
async def import_data(db: Session = Depends(get_db), file: UploadFile = File(...)):
    """Import game data from a JSON payload."""

    try:
        contents = await file.read()
        data = json.loads(contents)
        result = crud.import_game_data(db, data)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during import: {e}")
